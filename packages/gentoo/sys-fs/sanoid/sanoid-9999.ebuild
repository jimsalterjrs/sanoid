# Copyright 2019 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=7

EGIT_REPO_URI="https://github.com/jimsalterjrs/${PN}.git"
inherit git-r3

DESCRIPTION="Policy-driven snapshot management and replication tools for ZFS"
HOMEPAGE="https://github.com/jimsalterjrs/sanoid"

LICENSE="GPL-3.0"
SLOT="0"
KEYWORDS="**"
IUSE=""

DEPEND="app-arch/lzop
		dev-perl/Config-IniFiles
		dev-perl/Capture-Tiny
		sys-apps/pv
		sys-block/mbuffer
		virtual/perl-Data-Dumper"
RDEPEND="${DEPEND}"
BDEPEND=""

DOCS=( README.md )

src_install() {
	dobin findoid
	dobin sanoid
	dobin sleepymutex
	dobin syncoid
	keepdir /etc/${PN}
	insinto /etc/${PN}
	doins sanoid.conf
	doins sanoid.defaults.conf
	insinto /etc/cron.d
	newins "${FILESDIR}/${PN}.cron" ${PN}
}
