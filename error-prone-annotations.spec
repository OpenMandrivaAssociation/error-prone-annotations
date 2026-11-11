Name:		error-prone-annotations
Version:	2.52.0
Release:	2
Summary:	Annotations for Error Prone static analysis
Group:		Development/Java
License:	ASL 2.0
URL:		https://errorprone.info/
Source0:	https://github.com/google/error-prone/archive/refs/tags/v%{version}.tar.gz#/error-prone-%{version}.tar.gz
# Gradle 9.9.1 strictly pins 2.50.0. This tag archive has no prebuilt jars.
Source1:	https://github.com/google/error-prone/archive/refs/tags/v2.50.0.tar.gz#/error-prone-2.50.0.tar.gz

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
is multi-release and includes module-info. Gradle 9.9.1 strictly pins
2.50.0, so that jar is installed beside 2.52.0.

%prep
%autosetup -n error-prone-%{version}
%setup -q -T -D -a 1 -n error-prone-%{version}
find . -name '*.jar' -delete
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

%build -a
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java}"
mkdir -p ep250/classes
find error-prone-2.50.0/annotations/src/main/java -name '*.java' ! -name module-info.java > ep250/sources.list
test -s ep250/sources.list
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 -Xlint:-options \
	-d ep250/classes @ep250/sources.list
"$JAVA_HOME/bin/jar" cf ep250/error_prone_annotations.jar -C ep250/classes .
cat > ep250/error_prone_annotations.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.errorprone</groupId>
  <artifactId>error_prone_annotations</artifactId>
  <version>2.50.0</version>
  <name>error-prone annotations</name>
  <description>Annotations for Error Prone static analysis.</description>
  <url>https://errorprone.info/</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
</project>
EOF

%install -p
sysjar install --buildroot %{buildroot} \
	--artifact ep250/error_prone_annotations.pom:ep250/error_prone_annotations.jar \
	--file-name error_prone_annotations-2.50.0 \
	--filelist .mfiles250
# 2.52.0 owns error_prone_annotations.sysjar. 2.50.0 keeps a second index.
/bin/mv %{buildroot}/usr/share/sysjar/index/com.google.errorprone/error_prone_annotations.sysjar \
	%{buildroot}/usr/share/sysjar/index/com.google.errorprone/error_prone_annotations-2.50.0.sysjar
sed -i 's|/usr/share/sysjar/index/com.google.errorprone/error_prone_annotations\.sysjar|/usr/share/sysjar/index/com.google.errorprone/error_prone_annotations-2.50.0.sysjar|' .mfiles250

%install -a
while IFS= read -r line; do
	grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
done < .mfiles250

%check -a
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java}"
cat > EpSmoke.java << 'EOF'
import com.google.errorprone.annotations.CheckReturnValue;
public class EpSmoke {
	@CheckReturnValue
	static int value() {
		return 50;
	}
	public static void main(String[] args) {
		if (value() != 50) {
			throw new AssertionError(value());
		}
		System.out.println(args[0] + " " + CheckReturnValue.class.getSimpleName());
	}
}
EOF
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 -Xlint:-options \
	-cp %{buildroot}%{_javadir}/error_prone_annotations.jar EpSmoke.java
"$JAVA_HOME/bin/java" -cp "%{buildroot}%{_javadir}/error_prone_annotations.jar:." EpSmoke ep252_ok | tee check252.log
grep -F -q 'ep252_ok CheckReturnValue' check252.log
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 -Xlint:-options \
	-cp %{buildroot}%{_javadir}/error_prone_annotations-2.50.0.jar EpSmoke.java
"$JAVA_HOME/bin/java" -cp "%{buildroot}%{_javadir}/error_prone_annotations-2.50.0.jar:." EpSmoke ep250_ok | tee check250.log
grep -F -q 'ep250_ok CheckReturnValue' check250.log

%files -f .mfiles
%doc COPYING README.md
