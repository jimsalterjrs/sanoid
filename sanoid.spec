Name:		sanoid
Version:	1.4.4
Release:	1%{?dist}
BuildArch:	noarch
Summary:	A policy-driven snapshot management tool for ZFS filesystems

Group:		Applications/System
License:	GPLv3
URL:		https://github.com/jimsalterjrs/sanoid
Source0:	https://github.com/jimsalterjrs/sanoid/archive/sanoid-master.zip
Patch0:		sanoid-syncoid-sshkey.patch
#BuildRequires:	
Requires:	perl

%description
Sanoid is a policy-driven snapshot management
tool for ZFS filesystems. You can use Sanoid
to create, automatically thin, and monitor snapshots
and pool health from a single eminently
human-readable TOML config file.

%prep
%setup -q -n sanoid-master
%patch0 -p1

%build

%install
%{__install} -D -m 0644 sanoid.defaults.conf %{buildroot}/etc/sanoid/sanoid.defaults.conf
%{__install} -d %{buildroot}%{_sbindir}
%{__install} -m 0755 sanoid syncoid findoid sleepymutex %{buildroot}%{_sbindir}
%{__install} -D -m 0644 sanoid.conf %{buildroot}%{_docdir}/%{name}-%{version}/examples/sanoid.conf
echo "* * * * * root %{_sbindir}/sanoid --cron" > %{buildroot}%{_docdir}/%{name}-%{version}/examples/sanoid.cron

%files
%doc CHANGELIST LICENSE VERSION README.md
%{_sbindir}/sanoid
%{_sbindir}/syncoid
%{_sbindir}/findoid
%{_sbindir}/sleepymutex
%dir %{_sysconfdir}/%{name}
%config %{_sysconfdir}/%{name}/sanoid.defaults.conf



%changelog
* Sat Feb 13 2016 Thomas M. Lapp <tmlapp@gmail.com> - 1.4.4-1
- Initial RPM Package
