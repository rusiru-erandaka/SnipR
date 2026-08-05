#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
stage_dir=$(mktemp -d)
cleanup() {
    rm -rf -- "$stage_dir"
}
trap cleanup EXIT INT TERM

package_root="$stage_dir/sniplite"
mkdir -p "$package_root/DEBIAN"
mkdir -p "$package_root/usr/bin"
mkdir -p "$package_root/usr/lib/python3/dist-packages/sniplite"
mkdir -p "$package_root/usr/share/applications"
mkdir -p "$package_root/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$project_dir/dist"

install -m 0644 "$project_dir/data/deb-control" "$package_root/DEBIAN/control"
install -m 0755 "$project_dir/data/sniplite" "$package_root/usr/bin/sniplite"
install -m 0644 "$project_dir"/sniplite/*.py "$package_root/usr/lib/python3/dist-packages/sniplite/"
install -m 0644 "$project_dir/data/io.github.sniplite.Sniplite.desktop" "$package_root/usr/share/applications/"
install -m 0644 "$project_dir/data/io.github.sniplite.Sniplite.svg" "$package_root/usr/share/icons/hicolor/scalable/apps/"

dpkg-deb --build --root-owner-group "$package_root" "$project_dir/dist/sniplite_0.1.3-1_all.deb"
echo "Built $project_dir/dist/sniplite_0.1.3-1_all.deb"
