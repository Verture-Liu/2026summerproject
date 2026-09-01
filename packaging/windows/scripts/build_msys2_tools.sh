#!/usr/bin/env bash
set -euo pipefail

export PATH="/ucrt64/bin:${PATH}"

cache="$(cygpath -u "$1")"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="${cache}/msys2-work"
built="${cache}/built"
downloads="${cache}/downloads"
rm -rf "${work}"
mkdir -p "${work}" "${built}"

copy_runtime_dlls() {
  local executable="$1"
  local destination="$2"
  ldd "${executable}" | awk '/=> \/ucrt64\// {print $3}' | while read -r dependency; do
    cp -f "${dependency}" "${destination}/"
  done
}

tar -xzf "${downloads}/seqtk-v1.5.tar.gz" -C "${work}"
cp "${script_dir}/seqtk_mingw_compat.h" "${work}/seqtk-1.5/"
make -C "${work}/seqtk-1.5" CC=gcc CFLAGS="-g -Wall -O2 -Wno-unused-function -Wno-format -include seqtk_mingw_compat.h"
mkdir -p "${built}/seqtk"
cp "${work}/seqtk-1.5/seqtk.exe" "${built}/seqtk/"
copy_runtime_dlls "${built}/seqtk/seqtk.exe" "${built}/seqtk"

tar -xzf "${downloads}/bwa-v0.7.19.tar.gz" -C "${work}"
cp -R "${script_dir}/bwa_mingw_compat" "${work}/bwa-0.7.19/compat"
cp "${script_dir}/seqtk_mingw_compat.h" "${work}/bwa-0.7.19/"
cp "${script_dir}/bwa_mingw_compat/bwashm_stub.c" "${work}/bwa-0.7.19/bwashm.c"
cp "${script_dir}/bwa_mingw_compat/kopen_windows.c" "${work}/bwa-0.7.19/kopen.c"
make -C "${work}/bwa-0.7.19" CC=gcc CFLAGS="-g -Wall -Wno-unused-function -O3 -DHAVE_PTHREAD -DUSE_MALLOC_WRAPPERS -Icompat -include seqtk_mingw_compat.h"
mkdir -p "${built}/bwa"
cp "${work}/bwa-0.7.19/bwa.exe" "${built}/bwa/"
copy_runtime_dlls "${built}/bwa/bwa.exe" "${built}/bwa"

samtools_exe="/ucrt64/bin/samtools.exe"
samtools_version="$(${samtools_exe} --version | head -n 1 | awk '{print $2}')"
if [[ "${samtools_version}" != "1.24" ]]; then
  printf 'Expected MSYS2 Samtools 1.24, found %s\n' "${samtools_version}" >&2
  exit 1
fi
mkdir -p "${built}/samtools"
cp "${samtools_exe}" "${built}/samtools/"
copy_runtime_dlls "${built}/samtools/samtools.exe" "${built}/samtools"

printf 'Built seqtk, bwa and samtools in %s\n' "${built}"
