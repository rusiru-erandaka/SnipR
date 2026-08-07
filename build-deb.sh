#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
stage_dir=$(mktemp -d)
cleanup() {
    rm -rf -- "$stage_dir"
}
trap cleanup EXIT INT TERM

package_root="$stage_dir/snipr"
mkdir -p "$package_root/DEBIAN"
mkdir -p "$package_root/usr/bin"
mkdir -p "$package_root/usr/lib/python3/dist-packages/snipr"
mkdir -p "$package_root/usr/share/applications"
mkdir -p "$package_root/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$project_dir/dist"

install -m 0644 "$project_dir/data/deb-control" "$package_root/DEBIAN/control"
install -m 0755 "$project_dir/data/snipr" "$package_root/usr/bin/snipr"
install -m 0644 "$project_dir"/snipr/*.py "$package_root/usr/lib/python3/dist-packages/snipr/"
install -m 0644 "$project_dir/data/io.github.snipr.SnipR.desktop" "$package_root/usr/share/applications/"
install -m 0644 "$project_dir/data/io.github.snipr.SnipR.svg" "$package_root/usr/share/icons/hicolor/scalable/apps/"

dpkg-deb --build --root-owner-group "$package_root" "$project_dir/dist/snipr_0.3.0-1_all.deb"
echo "Built $project_dir/dist/snipr_0.3.0-1_all.deb"
