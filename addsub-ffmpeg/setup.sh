#!/usr/bin/env bash
set -Eeuo pipefail

project_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(CDPATH= cd -- "$project_dir/.." && pwd)"
ffmpeg_bin_dir="$repository_root/.tools/ffmpeg/bin"
ffmpeg_executable="$ffmpeg_bin_dir/ffmpeg"
ffprobe_executable="$ffmpeg_bin_dir/ffprobe"
force_ffmpeg=0
temporary_directory=''

step() {
    printf '\n==> %s\n' "$1"
}

fail() {
    printf 'Error: %s\n' "$1" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Usage: ./setup.sh [--force-ffmpeg]

  --force-ffmpeg  Download and replace the project-local FFmpeg binaries.
  -h, --help      Show this help message.
EOF
}

cleanup() {
    if [ -n "$temporary_directory" ] && [ -d "$temporary_directory" ]; then
        rm -rf -- "$temporary_directory"
    fi
}

download_file() {
    local url="$1"
    local destination="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fL --retry 3 --connect-timeout 30 -o "$destination" "$url"
    elif command -v wget >/dev/null 2>&1; then
        wget --tries=3 --timeout=30 -O "$destination" "$url"
    else
        fail 'curl or wget is required to download setup files.'
    fi
}

sha256_file() {
    local file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | awk '{print $1}'
    elif command -v openssl >/dev/null 2>&1; then
        openssl dgst -sha256 "$file" | awk '{print $NF}'
    else
        fail 'sha256sum, shasum, or openssl is required to verify FFmpeg.'
    fi
}

verify_sha256() {
    local file="$1"
    local expected="$2"
    local actual
    actual="$(sha256_file "$file" | tr '[:upper:]' '[:lower:]')"
    if [[ ! "$expected" =~ ^[0-9a-f]{64}$ ]]; then
        fail "Invalid SHA-256 checksum returned for $(basename "$file")."
    fi
    if [ "$actual" != "$expected" ]; then
        fail "SHA-256 verification failed for $(basename "$file")."
    fi
}

extract_zip() {
    local archive="$1"
    local destination="$2"
    mkdir -p "$destination"
    if command -v unzip >/dev/null 2>&1; then
        unzip -q "$archive" -d "$destination"
    elif [ "$(uname -s)" = 'Darwin' ] && command -v ditto >/dev/null 2>&1; then
        ditto -x -k "$archive" "$destination"
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m zipfile -e "$archive" "$destination"
    elif command -v tar >/dev/null 2>&1 && tar -tf "$archive" >/dev/null 2>&1; then
        tar -xf "$archive" -C "$destination"
    else
        fail 'unzip, Python 3, or a ZIP-capable tar command is required to extract FFmpeg.'
    fi
}

install_uv() {
    if command -v uv >/dev/null 2>&1; then
        printf 'uv is already available: %s\n' "$(command -v uv)"
        return
    fi

    step 'Installing uv with the official Astral installer'
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        fail 'curl or wget is required to install uv.'
    fi

    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    command -v uv >/dev/null 2>&1 ||
        fail 'uv was installed but is not on PATH. Open a new terminal and run setup.sh again.'
}

install_ffmpeg() {
    if [ "$force_ffmpeg" -eq 0 ] && [ -x "$ffmpeg_executable" ] && [ -x "$ffprobe_executable" ]; then
        printf 'Project FFmpeg is already available: %s\n' "$ffmpeg_executable"
        return
    fi

    local platform
    local architecture
    local release_path
    local ffmpeg_checksum
    local ffprobe_checksum
    case "$(uname -s)" in
        Darwin)
            platform='macos'
            ;;
        Linux)
            platform='linux'
            ;;
        *)
            fail 'Unsupported operating system. On Windows, run setup.ps1 instead.'
            ;;
    esac

    case "$(uname -m)" in
        x86_64|amd64)
            architecture='amd64'
            ;;
        arm64|aarch64)
            architecture='arm64'
            ;;
        *)
            fail "Unsupported CPU architecture: $(uname -m)."
            ;;
    esac

    case "$platform/$architecture" in
        linux/amd64)
            release_path='linux/amd64/1789931100_9.0.2'
            ffmpeg_checksum='fa8ecf4abbd290d98f7d188b8649cc6b391ae209a98452be955a15aab1909d7f'
            ffprobe_checksum='3f428c49070be3d24ec338602b76d412e401ffcb8a5641ef0e729181a232fc32'
            ;;
        linux/arm64)
            release_path='linux/arm64/1789931697_9.0.2'
            ffmpeg_checksum='93a76ae90db5474eecdf951a729857c64f3de23567228d6a7d5e6e8e3cd1021b'
            ffprobe_checksum='bcbe80fb741c180083327afaf5434812e006b33cacde2016b9aeaf6936128330'
            ;;
        macos/amd64)
            release_path='macos/amd64/1789931006_9.0.2'
            ffmpeg_checksum='7c6b4125b191cbf773832dc51f424cf2b6bb7da43007d1e066f95909e47cacd4'
            ffprobe_checksum='2322438ed2f6319a691291b247d09c69dcaa3a982460d1f269a7e1af335cfdfd'
            ;;
        macos/arm64)
            release_path='macos/arm64/1789931890_9.0.2'
            ffmpeg_checksum='c8ed4c4e6978a03c485edbfe4e0a5dc2380f8a30bba5150531b31b094492d924'
            ffprobe_checksum='fcbe839537485eaee7a7a8bc5cbc0f90d53617e80943e8a5b2e31cb851197ea6'
            ;;
    esac

    step "Installing portable FFmpeg 9.0.2 for $platform/$architecture"
    local base_url="https://ffmpeg.martin-riedl.de/download/$release_path"
    local tool
    local archive
    local expected_checksum
    local extract_directory
    local downloaded_executable
    mkdir -p "$ffmpeg_bin_dir"

    for tool in ffmpeg ffprobe; do
        archive="$temporary_directory/$tool.zip"
        extract_directory="$temporary_directory/$tool-extracted"
        if [ "$tool" = 'ffmpeg' ]; then
            expected_checksum="$ffmpeg_checksum"
        else
            expected_checksum="$ffprobe_checksum"
        fi
        download_file "$base_url/$tool.zip" "$archive"
        verify_sha256 "$archive" "$expected_checksum"
        extract_zip "$archive" "$extract_directory"
        downloaded_executable="$(find "$extract_directory" -type f -name "$tool" -print -quit)"
        [ -n "$downloaded_executable" ] || fail "$tool was not found in the downloaded archive."
        cp "$downloaded_executable" "$ffmpeg_bin_dir/$tool"
        chmod 0755 "$ffmpeg_bin_dir/$tool"
    done

    if [ "$platform" = 'macos' ] && command -v xattr >/dev/null 2>&1; then
        xattr -d com.apple.quarantine "$ffmpeg_executable" "$ffprobe_executable" 2>/dev/null || true
    fi

    "$ffmpeg_executable" -version | sed -n '1p'
    "$ffprobe_executable" -version | sed -n '1p'
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --force-ffmpeg)
            force_ffmpeg=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            fail "Unknown option: $1"
            ;;
    esac
    shift
done

temporary_directory="$(mktemp -d "${TMPDIR:-/tmp}/addsub-ffmpeg-setup.XXXXXX")"
trap cleanup EXIT

install_ffmpeg
install_uv

step 'Installing Python dependencies'
(
    cd "$project_dir"
    uv sync
)

step 'Setup complete'
printf 'Open a new terminal, then run the program from this directory with:\n  uv run main.py\n'
