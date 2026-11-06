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
# The Java 9 execution has a goal and no phase, so Maven never runs it.
# default-compile is source 8 and still compiles module-info.java.
java9 = """<execution>
            <id>compile-java9</id>
            <phase>compile</phase>
            <goals>
              <goal>compile</goal>
            </goals>
            <configuration>
              <release>9</release>
              <compileSourceRoots>
                <compileSourceRoot>${project.basedir}/src/main/java9</compileSourceRoot>
              </compileSourceRoots>
              <multiReleaseOutput>true</multiReleaseOutput>
            </configuration>
          </execution>"""
text, n = re.subn(
    r"<execution>\s*<id>compile-java9</id>.*?</execution>",
    java9,
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit(f"java9 execution {n}")
Path("pom.xml").write_text(text)
shutil.rmtree("src", ignore_errors=True)
shutil.move("annotations/src", "src")
module_info = Path("src/main/java/module-info.java")
if not module_info.is_file():
    raise SystemExit("module-info missing")
java9_dir = Path("src/main/java9")
java9_dir.mkdir()
module_info.rename(java9_dir / "module-info.java")
PY

%files -f .mfiles
%doc COPYING README.md
