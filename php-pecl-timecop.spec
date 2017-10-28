#
# Conditional build:
%bcond_without	tests		# build without tests

%define		php_name	php%{?php_suffix}
%define		modname	timecop
Summary:	Time travel and freezing extension
Name:		%{php_name}-pecl-%{modname}
Version:	1.2.8
Release:	1
License:	MIT
Group:		Development/Languages
Source0:	https://pecl.php.net/get/%{modname}-%{version}.tgz
# Source0-md5:	35a5026fb16645b29b4e8ad88a0f558d
Source1:	%{modname}.ini
URL:		https://pecl.php.net/package/timecop/
BuildRequires:	%{php_name}-cli
BuildRequires:	%{php_name}-devel
BuildRequires:	rpmbuild(macros) >= 1.666
%if %{with tests}
BuildRequires:	%{php_name}-pcre
%endif
%{?requires_php_extension}
Provides:	php(%{modname}) = %{version}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
A PHP extension providing "time travel" and "time freezing"
capabilities, inspired by ruby timecop gem.

%prep
%setup -qc
mv %{modname}-%{version}/* .

cat <<'EOF' > run-tests.sh
#!/bin/sh
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
exec %{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="" \
	RUN_TESTS_SETTINGS="-q $*"
EOF
chmod +x run-tests.sh

%build
# Sanity check, really often broken
extver=$(sed -n '/#define PHP_TIMECOP_VERSION/{s/.* "//;s/".*$//;p}' php_timecop.h)
if test "x${extver}" != "x%{version}"; then
	: Error: Upstream extension version is ${extver}, expecting %{version}.
	exit 1
fi

phpize
%configure \
	--with-libdir=%{_lib} \
	--enable-timecop
%{__make}

# simple module load test
%{__php} -n -q \
	-d extension_dir=modules \
	-d extension=%{modname}.so \
	-m > modules.log
grep %{modname} modules.log

%if %{with tests}
./run-tests.sh
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	INSTALL_ROOT=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d/%{modname}.ini

%clean
rm -rf $RPM_BUILD_ROOT

%post
%php_webserver_restart

%postun
if [ "$1" = 0 ]; then
	%php_webserver_restart
fi

%files
%defattr(644,root,root,755)
%doc LICENSE
%config(noreplace) %verify(not md5 mtime size) %{php_sysconfdir}/conf.d/%{modname}.ini
%attr(755,root,root) %{php_extensiondir}/%{modname}.so
