Name:		error-prone-annotations
Version:	2.52.0
Release:	1
Summary:	Annotations for Error Prone static analysis
Group:		Development/Java
License:	ASL 2.0
URL:		https://errorprone.info/
Source0:	https://github.com/google/error-prone/archive/refs/tags/v%{version}.tar.gz#/error-prone-%{version}.tar.gz

BuildArch:	noarch
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name error_prone_annotations --link %{name}

%description
Error Prone annotations mark APIs for the Error Prone checker, including
CheckReturnValue, Immutable, and GuardedBy. This package is the
annotation jar from 2.52.0. The checker itself is not packaged. The jar
is multi-release and includes module-info.

%prep
%autosetup -n error-prone-%{version}
# Build only the annotations module. error_prone_parent and bnd are not
# packaged. source and target next to release make javac fail.
python - <<'PY'
import re
import shutil
from pathlib import Path

text = Path("annotations/pom.xml").read_text()
text, n = re.subn(r"\s*<parent>.*?</parent>", "\n", text, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"parent {n}")
old = "  <name>error-prone annotations</name>\n  <artifactId>error_prone_annotations</artifactId>"
new = """  <groupId>com.google.errorprone</groupId>
  <artifactId>error_prone_annotations</artifactId>
  <version>%{version}</version>
  <name>error-prone annotations</name>"""
if old not in text:
    raise SystemExit("artifact block missing")
text = text.replace(old, new, 1)
text, n = re.subn(
    r"\s*<dependency>\s*<groupId>junit</groupId>.*?</dependency>",
    "",
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit(f"junit {n}")
text, n = re.subn(
    r"\s*<plugin>\s*<groupId>biz\.aQute\.bnd</groupId>.*?</plugin>",
    "",
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit(f"bnd {n}")
old9 = "              <source>9</source>\n              <target>9</target>\n              <release>9</release>"
new9 = "              <release>9</release>"
if old9 not in text:
    raise SystemExit("java 9 levels missing")
text = text.replace(old9, new9, 1)
Path("pom.xml").write_text(text)
shutil.rmtree("src", ignore_errors=True)
shutil.move("annotations/src", "src")
PY

%files -f .mfiles
%doc COPYING README.md
