#!/usr/bin/env bash
set -euo pipefail

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
make -C "${work}/bwa-0.7.19" CC=gcc CFLAGS="-g -Wall -Wno-unused-function -O3 -DHAVE_PTHREAD -DUSE_MALLOC_WRAPPERS -Icompat -include seqtk_mingw_compat.h"
mkdir -p "${built}/bwa"
cp "${work}/bwa-0.7.19/bwa.exe" "${built}/bwa/"
copy_runtime_dlls "${built}/bwa/bwa.exe" "${built}/bwa"

tar -xjf "${downloads}/samtools-1.23.1.tar.bz2" -C "${work}"
pushd "${work}/samtools-1.23.1" >/dev/null
chmod +x version.sh htslib-1.23.1/version.sh htslib-1.23.1/hts_probe_cc.sh
./configure --without-curses --disable-lzma --disable-bz2 --without-libdeflate
make -j2
popd >/dev/null
mkdir -p "${built}/samtools"
cp "${work}/samtools-1.23.1/samtools.exe" "${built}/samtools/"
copy_runtime_dlls "${built}/samtools/samtools.exe" "${built}/samtools"

printf 'Built seqtk, bwa and samtools in %s\n' "${built}"
