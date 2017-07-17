%global version 1.4.13
%global git_tag v%{version}

Name:		sanoid
Version:	%{version}
Release:	1%{?dist}
BuildArch:	noarch
Summary:	A policy-driven snapshot management tool for ZFS file systems
Group:		Applications/System
License:	GPLv3
URL:		https://github.com/jimsalterjrs/sanoid
Source0:  https://github.com/jimsalterjrs/%{name}/archive/%{git_tag}/%{name}-%{version}.tar.gz
#BuildRequires:	
Requires:	perl, mbuffer, lzop, pv

%description
Sanoid is a policy-driven snapshot management
tool for ZFS file systems. You can use Sanoid
to create, automatically thin, and monitor snapshots
and pool health from a single eminently
human-readable TOML configuration file.

%prep
%setup -q

%build

%install
%{__install} -D -m 0644 sanoid.defaults.conf %{buildroot}/etc/sanoid/sanoid.defaults.conf
%{__install} -d %{buildroot}%{_sbindir}
%{__install} -m 0755 sanoid syncoid findoid sleepymutex %{buildroot}%{_sbindir}

%if 0%{?fedora}
%{__install} -D -m 0644 sanoid.conf %{buildroot}%{_docdir}/%{name}/examples/sanoid.conf
echo "* * * * * root %{_sbindir}/sanoid --cron" > %{buildroot}%{_docdir}/%{name}/examples/sanoid.cron
%endif
%if 0%{?rhel}
%{__install} -D -m 0644 sanoid.conf %{buildroot}%{_docdir}/%{name}-%{version}/examples/sanoid.conf
echo "* * * * * root %{_sbindir}/sanoid --cron" > %{buildroot}%{_docdir}/%{name}-%{version}/examples/sanoid.cron
%endif

%files
%doc CHANGELIST VERSION README.md FREEBSD.readme
%license LICENSE
%{_sbindir}/sanoid
%{_sbindir}/syncoid
%{_sbindir}/findoid
%{_sbindir}/sleepymutex
%dir %{_sysconfdir}/%{name}
%config %{_sysconfdir}/%{name}/sanoid.defaults.conf
%if 0%{?fedora}
%{_docdir}/%{name}
%endif
%if 0%{?rhel}
%{_docdir}/%{name}-%{version}
%endif

%changelog
* Wed Jul 12 2017 Thomas M. Lapp <tmlapp@gmail.com> - 1.4.13-1
- Version bump
- Include FREEBSD.readme in docs
* Wed Jul 12 2017 Thomas M. Lapp <tmlapp@gmail.com> - 1.4.9-1
- Version bump
- Clean up variables and macros
- Compatible with both Fedora and Red Hat

* Sat Feb 13 2016 Thomas M. Lapp <tmlapp@gmail.com> - 1.4.4-1
- Initial RPM Package
