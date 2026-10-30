#!/usr/bin/env python3
"""Render the Pifrost set, chozian opinions mixin, and DoD CA mixin.

The main descriptor is a v3 ``kind: set`` that composes Docker's published
shell workload with the project-owned Pi 1.5.0 mixin. The set contributes the Bifrost
network policy, lifecycle setup, and shell environment. The Pi mixin carries the
pinned Bifrost provider extension. The optional opinions mixin contributes the
reviewed shell/editor files and current Pi settings snapshot. Host Pi
configuration is an explicit opt-in. The optional certificate mixin keeps
certificate bytes in its own image layer.
"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sbx-kit-pifrost.yaml"
OPINIONS_OUT = ROOT / "sbx-kit-pifrost-opinions-chozian.yaml"
HOST_PI_AGENT = Path.home() / ".pi" / "agent"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--use-host-pi-config",
    action="store_true",
    help="explicitly use matching files from ~/.pi/agent instead of snapshots",
)
ARGS = parser.parse_args()


def pi_config_source(name: str) -> Path:
    """Choose a checked-in snapshot unless host config use was requested."""
    host_source = HOST_PI_AGENT / name
    if ARGS.use_host_pi_config and host_source.is_file():
        return host_source
    return ROOT / "files" / name


SIMPLE_ENGLISH_FILES = [
    "SKILL.md",
    "references/rule-catalog.md",
    "references/strict-vocabulary.md",
    "references/use-cases.md",
    "references/word-swaps.md",
]
SIMPLE_ENGLISH_BUNDLE_PATH = "/usr/local/share/sbx-kit-pifrost-opinions/simple-english"

OPINION_FILES = [
    ("/etc/sandbox-persistent.sh", ROOT / "files/sandbox-persistent.sh", "0644", "Persistent shell environment"),
    ("/home/agent/.bashrc", ROOT / "files/.bashrc", "0644", "Bash configuration"),
    ("/home/agent/.bash_aliases", ROOT / "files/.bash_aliases", "0644", "Bash aliases"),
    ("/home/agent/.dircolors", ROOT / "files/.dircolors", "0644", "Dircolors"),
    ("/home/agent/.vimrc", ROOT / "files/.vimrc", "0644", "Vim configuration"),
    ("/home/agent/.pi/agent/settings.json", pi_config_source("settings.json"), "0644", "Pi settings"),
]

SIMPLE_ENGLISH_ROOT = ROOT / "vendor/simple-english"
for relative in [
    "LICENSE",
    "SOURCE.txt",
    *(f"skills/simple-english/{relative}" for relative in SIMPLE_ENGLISH_FILES),
]:
    source = SIMPLE_ENGLISH_ROOT / relative
    if not source.is_file():
        raise SystemExit(f"missing Simple English source file: {source}")

CERTIFICATES = (
    "5301-PA5260-Core.ds.amrdec.army.mil.crt",
    "DoD_v5.14.crt",
)
DOD_CERT_OUT = ROOT / "sbx-kit-pifrost-certs-dod.yaml"
DOD_DOCKERFILE_OUT = ROOT / "sbx-kit-pifrost-certs-dod.dockerfile"

SET_VERSION = "1.0.0"
OPINIONS_VERSION = "1.0.0"
DOD_VERSION = "1.0.0"
SHELL_REF = "docker.io/sbx/shell:1.0.3"
PI_MIXIN_REF = "docker.io/choziandi/sbx-kit-pifrost-pi-mixin:1.5.0"
PI_MIXIN_VERSION = "1.5.0"
BIFROST_PROVIDER_VERSION = "0.2.0"
BIFROST_URL = "http://host.docker.internal:8080/v1"
PI_MIXIN_DOCKERFILE = ROOT / "templates/pifrost-pi-mixin.dockerfile"
PI_MIXIN_OUT = ROOT / "sbx-kit-pifrost-pi-mixin.dockerfile"
PI_MIXIN_KIT_OUT = ROOT / "sbx-kit-pifrost-pi-mixin.yaml"

# These are the network entries in Docker Sandboxes v0.50.1's bundled local
# policy. The ai-services group is deliberately excluded from the allow set
# below except for models.dev, which Pi uses for runtime model metadata. The
# remaining entries are denied explicitly. Keep this snapshot synchronized
# when the bundled local policy changes in a newer Sandbox release.
DEFAULT_LOCAL_POLICY_ALLOW_GROUPS = {
    "default-ai-services": (
        "api.anthropic.com:443",
        "statsig.anthropic.com:443",
        "platform.claude.com:443",
        "mcp-proxy.anthropic.com:443",
        "downloads.claude.ai:443",
        "claude.com:443",
        "bridge.claudeusercontent.com:443",
        "**.openai.com:443",
        "chatgpt.com:443",
        "**.chatgpt.com:443",
        "**.oaistatic.com:443",
        "**.oaiusercontent.com:443",
        "cdn.openaimerge.com:443",
        "cursor.com:443",
        "**.cursor.sh:443",
        "gemini.google.com:443",
        "generativelanguage.googleapis.com:443",
        "play.googleapis.com:443",
        "api.perplexity.ai:443",
        "models.dev:443",
        "factory.ai:443",
        "**.factory.ai:443",
        "api.workos.com:443",
    ),
    "default-package-managers": (
        "registry.npmjs.org:443",
        "npmjs.com:443",
        "npmjs.org:443",
        "npm.duckdb.org:443",
        "yarnpkg.com:443",
        "**.yarnpkg.com:443",
        "nodejs.org:443",
        "deb.nodesource.com:443",
        "bun.sh:443",
        "**.bun.sh:443",
        "pypi.org:443",
        "pypi.python.org:443",
        "files.pythonhosted.org:443",
        "pythonhosted.org:443",
        "pypa.io:443",
        "bootstrap.pypa.io:443",
        "astral.sh:443",
        "crates.io:443",
        "index.crates.io:443",
        "static.crates.io:443",
        "rustup.rs:443",
        "sh.rustup.rs:443",
        "static.rust-lang.org:443",
        "golang.org:443",
        "goproxy.io:443",
        "proxy.golang.org:443",
        "sum.golang.org:443",
        "pkg.go.dev:443",
        "maven.org:443",
        "repo.maven.apache.org:443",
        "gradle.org:443",
        "**.gradle.org:443",
        "spring.io:443",
        "java.com:443",
        "java.net:443",
        "packagist.org:443",
        "**.packagist.org:443",
        "packagist.com:443",
        "rubygems.org:443",
        "ruby-lang.org:443",
        "rubyonrails.org:443",
        "rvm.io:443",
        "nuget.org:443",
        "dot.net:443",
        "dotnet.microsoft.com:443",
        "pub.dev:443",
        "hex.pm:443",
        "cpan.org:443",
        "metacpan.org:443",
        "haskell.org:443",
        "swift.org:443",
        "cocoapods.org:443",
        "ziglang.org:443",
        "apache.org:443",
        "eclipse.org:443",
        "tuf-repo-cdn.sigstore.dev:443",
    ),
    "default-code-and-containers": (
        "github.com:443",
        "**.github.com:443",
        "**.githubusercontent.com:443",
        "gitlab.com:443",
        "**.gitlab.com:443",
        "bitbucket.org:443",
        "sourceforge.net:443",
        "launchpad.net:443",
        "ppa.launchpad.net:443",
        "docker.io:443",
        "**.docker.io:443",
        "docker.com:443",
        "**.docker.com:443",
        "production.cloudflare.docker.com:443",
        "**.production.cloudflare.docker.com:443",
        "production.cloudfront.docker.com:443",
        "**.production.cloudfront.docker.com:443",
        "docker-images-prod.6aa30f8b08e16409b46e0173d6de2f56.r2.cloudflarestorage.com:443",
        "dhi.io:443",
        "dhi.io:80",
        "ghcr.io:443",
        "gcr.io:443",
        "**.gcr.io:443",
        "mcr.microsoft.com:443",
        "**.data.mcr.microsoft.com:443",
        "quay.io:443",
        "registry.k8s.io:443",
        "k8s.io:443",
        "public.ecr.aws:443",
        "d2glxqk2uabbnd.cloudfront.net:443",
        "**.githubcopilot.com:443",
        "code.visualstudio.com:443",
        "vscode.dev:443",
        "vscode.download.prss.microsoft.com:443",
    ),
    "default-os-packages": (
        "archive.ubuntu.com:443",
        "archive.ubuntu.com:80",
        "security.ubuntu.com:443",
        "security.ubuntu.com:80",
        "ports.ubuntu.com:443",
        "ports.ubuntu.com:80",
        "ubuntu.com:443",
        "debian.org:443",
        "**.debian.org:443",
        "archlinux.org:443",
        "alpinelinux.org:443",
        "dl-cdn.alpinelinux.org:443",
        "centos.org:443",
        "fedoraproject.org:443",
        "apt.llvm.org:443",
        "packagecloud.io:443",
    ),
    "default-cert-validation": (
        "**.lencr.org:80",
        "**.lencr.org:443",
        "ocsp.digicert.com:80",
        "crl*.digicert.com:80",
        "cacerts.digicert.com:80",
        "*.one.digicert.com:80",
        "*.one.au.digicert.com:80",
        "*.one.ch.digicert.com:80",
        "*.one.nl.digicert.com:80",
        "*.one.digicert.co.jp:80",
        "ocsp.sectigo.com:80",
        "crl.sectigo.com:80",
        "crt.sectigo.com:80",
        "ocsp.comodoca.com:80",
        "crl.comodoca.com:80",
        "ocsp.usertrust.com:80",
        "crl.usertrust.com:80",
        "**.pki.goog:80",
        "**.pki.goog:443",
        "**.amazontrust.com:80",
        "**.amazontrust.com:443",
        "isrg.trustid.ocsp.identrust.com:80",
        "**.pki.microsoft.com:80",
        "**.pki.microsoft.com:443",
        "crl.globalsign.com:80",
        "crl.globalsign.net:80",
        "ocsp.globalsign.com:80",
        "ocsp.globalsign.com:443",
        "ocsp2.globalsign.com:80",
        "ocsp2.globalsign.com:443",
    ),
}

DEFAULT_LOCAL_POLICY_CLOUD_ENTRIES = (
    "**.amazonaws.com:443",
    "**.googleapis.com:443",
    "azure.com:443",
    "dev.azure.com:443",
    "login.microsoftonline.com:443",
    "**.blob.core.windows.net:443",
    "visualstudio.com:443",
    "**.visualstudio.com:443",
    "packages.microsoft.com:443",
    "hashicorp.com:443",
    "**.hashicorp.com:443",
    "vercel.com:443",
    "**.public.blob.vercel-storage.com:443",
    "challenges.cloudflare.com:443",
    "fastly.com:443",
    "unpkg.com:443",
    "jsdelivr.net:443",
    "**.gvt1.com:443",
    "dl.google.com:443",
    "binaries.prisma.sh:443",
    "playwright.azureedge.net:443",
    "cdn.playwright.dev:443",
    "mise.run:443",
    "mise-versions.jdx.dev:443",
    "json-schema.org:443",
    "json.schemastore.org:443",
    "**.gstatic.com:443",
    "**.googleusercontent.com:443",
    "apis.google.com:443",
    "play.google.com:443",
    "www.google.com:443",
    "csp.withgoogle.com:443",
    "supabase.com:443",
    "clerk.com:443",
    "figma.com:443",
    "app.daytona.io:443",
)

# Keep the named groups explicit: all bundled default groups are allowed except
# default-ai-services, while default-cloud-infrastructure remains allowed.
DEFAULT_LOCAL_POLICY_AI_SERVICES_DENY = tuple(
    entry
    for entry in DEFAULT_LOCAL_POLICY_ALLOW_GROUPS.pop("default-ai-services")
    if entry != "models.dev:443"
)
DEFAULT_LOCAL_POLICY_ALLOW_GROUPS["default-cloud-infrastructure"] = (
    DEFAULT_LOCAL_POLICY_CLOUD_ENTRIES
)


def yaml_block(text: str, indent: str = "        ") -> list[str]:
    # All inputs are text files and deliberately retain their final newline.
    lines = text.splitlines()
    return [indent + line if line else "" for line in lines] or [indent]


def file_entry(path: str, source: Path, mode: str, description: str) -> list[str]:
    return [
        f"        - path: {path}",
        f"          mode: \"{mode}\"",
        f"          description: {description}",
        "          content: |",
        *yaml_block(source.read_text(), indent="            "),
    ]


# The upstream shell and Pi mixin each provide guidance. This set contributes
# the repository's Bifrost-specific guidance in addition to those profiles.
AGENT_CONTEXT = """This sandbox is a generic shell workload with Pi installed.

The shell provides bash, git, apt, Docker (compose/buildx), curl, gh, jq, make,
gcc, Python 3, Node/npm, tmux, vim, and htop. Install additional packages with
apt when needed.

Run `pi` to start the coding agent. The Pifrost network policy provides the
host-local Bifrost route, and the core lifecycle supplies BIFROST_URL to shell
processes. The bundled Pi mixin includes the pinned pi-bifrost-provider
extension, which discovers the available models from Bifrost. The optional
`sbx-kit-pifrost-opinions-chozian` mixin supplies the current Pi settings
profile and shell preferences. The Bifrost credential is supplied through a
host-side custom secret; do not print or reconfigure the sentinel value.
The optional DoD certificate mixin adds only the approved certificates
requested at sandbox creation.

The sandbox's workspace is the project directory supplied to `sbx run`. Keep
changes inside that workspace unless the user explicitly asks otherwise.
"""

OPINIONS_CONTEXT = """This optional mixin supplies chozian's current Pi and shell preferences.

It provides the `simple-english` skill. Invoke it with
`/skill:simple-english` when needed.

It installs Bash completion and Solarized Vim support. The core Pifrost set
provides the Python 3 compatibility command `python`, BIFROST_URL, and the
Bifrost provider extension through the bundled Pi mixin. The selected Shell
workload already provides htop, less, tmux, and vim; this mixin does not
reinstall those packages. It also installs the reviewed files under `files/`,
including the current Pi settings snapshot and shell/editor configuration.

The Bifrost credential remains host-side. Do not print or reconfigure its
sentinel value.
"""


lines = [
    "# syntax=docker/sandbox-kit:3",
    "# yaml-language-server: $schema=https://raw.githubusercontent.com/docker/sandbox-kit-spec/main/schema/kit.schema.json",
    "# Generated by scripts/render-kit-set.py.",
    "#",
    "# This is a Shell + Pi kit set with the Pifrost Bifrost policy and",
    "# lifecycle configuration. chozian's files and Pi profile are supplied",
    "# by the separate optional opinions mixin.",
    "schemaVersion: \"3\"",
    "displayName: SBX Kit Shell + Pi",
    "author: \"chozian\"",
    "description: >-",
    "  A Docker Sandbox shell plus the project-owned Pi 1.5.0 mixin, with a protected",
    "  Bifrost connection and fail-closed direct-provider policy.",
    "licenses: [MIT]",
    "kind: set",
    f"version: \"{SET_VERSION}\"",
    "kits:",
    f"  - ref: {SHELL_REF}",
    f"  - ref: {PI_MIXIN_REF}",
    "",
    "# The set contributes these local capabilities in addition to the two",
    "# published kits above.",
    "capabilities:",
    "  - type: com.docker.sandbox/agent-context@1",
    "    config:",
    "      content: |",
    *yaml_block(AGENT_CONTEXT, indent="        "),
    "",
    "  # The package hook is intentionally create-time: Debian packages and",
    "  # their dpkg state cannot be made into a portable mixin overlay.",
    "  - type: com.docker.sandbox/network-policy@1",
    "    config:",
    "      install:",
    "        allow:",
    "          - deb.debian.org",
    "          - dhi.io",
    "      runtime:",
    "        allow:",
    "          - localhost:8080",
    "          - \"deb.debian.org:80\"",
    "          - host.docker.internal:8080",
    "          - pi.dev:443",
    "          # models.dev is the sole permitted host from default-ai-services.",
    "          - models.dev:443",
]

for group, entries in DEFAULT_LOCAL_POLICY_ALLOW_GROUPS.items():
    lines.append(f"        # {group} from Docker Sandboxes' bundled local policy.")
    lines.extend(f'          - "{entry}"' for entry in entries)

lines.extend([
    "        # Exclude the bundled default-ai-services group.",
    "        # Deny wins over allows contributed by an included kit.",
    "        deny:",
])
lines.extend(f'          - "{entry}"' for entry in DEFAULT_LOCAL_POLICY_AI_SERVICES_DENY)

lines.extend([
    "",
    "  - type: com.docker.sandbox/lifecycle@1",
    "    config:",
    "      install:",
    "        - user: \"0\"",
    "          description: Provide the Python 3 compatibility command",
    "          command: >-",
    "            set -eu; apt-get update -qq; DEBIAN_FRONTEND=noninteractive",
    "            apt-get install -y --no-install-recommends python-is-python3;",
    "            update-alternatives --install /usr/bin/pager pager /usr/bin/less 100;",
    "            update-alternatives --set pager /usr/bin/less;",
    "            apt-get clean; rm -rf /var/lib/apt/lists/*; command -v less; command -v pager;",
    "            test \"$(readlink -f /usr/bin/pager)\" = /usr/bin/less; command -v python3;",
    "            python3 --version; command -v python; python --version",
    "",
    "      # Apply after optional mixin file capabilities so the opinions",
    "      # mixin cannot replace the core Bifrost environment setup.",
    "      startup:",
    "        - user: \"0\"",
    "          description: Ensure the core Bifrost URL is available to shell-launched Pi processes",
    "          command: >-",
    '            set -eu; file=/etc/sandbox-persistent.sh; marker="# sbx-kit-pifrost: BIFROST_URL";',
    '            if ! grep -Fqx "$marker" "$file" 2>/dev/null && ! grep -Eq "^[[:space:]]*(export[[:space:]]+)?BIFROST_URL=" "$file" 2>/dev/null; then',
    f'''            printf '\\n%s\\nif [ -z "${{BIFROST_URL:-}}" ]; then\\n    export BIFROST_URL="{BIFROST_URL}"\\nfi\\n' "$marker" >> "$file";''',
    "            fi",
])

OUT.write_text("\n".join(lines) + "\n")

# The project-owned Pi mixin keeps the upstream overlay recipe but pins Pi at
# build time. It intentionally does not carry the upstream Anthropic credential
# capability; Pifrost routes model traffic through Bifrost instead.
pi_mixin_lines = [
    "# syntax=docker/sandbox-kit:3",
    "# Generated by scripts/render-kit-set.py from templates/pifrost-pi-mixin.dockerfile.",
    "schemaVersion: \"3\"",
    "displayName: Pi 1.5.0 (mixin)",
    "author: \"chozian\"",
    "description: >-",
    "  Pi 1.5.0 as a project-owned mixin, including the fd binary required by",
    "  Pi's find tool, npm runtime configuration, and the pinned Bifrost",
    "  provider extension.",
    "sourceUrl: https://github.com/lxdlam/pi-bifrost-provider",
    "kind: mixin",
    f"version: \"{PI_MIXIN_VERSION}\"",
    f"dockerfile: {PI_MIXIN_OUT.name}",
    "args:",
    "  version:",
    f"    default: \"{PI_MIXIN_VERSION}\"",
    "    pattern: '^[0-9]+\\.[0-9]+\\.[0-9]+$'",
    "    description: Pi release to install",
    "    buildArg: PI_VERSION",
    "  bifrostProviderVersion:",
    f"    default: \"{BIFROST_PROVIDER_VERSION}\"",
    "    pattern: '^[0-9]+\\.[0-9]+\\.[0-9]+$'",
    "    description: pi-bifrost-provider release to install",
    "    buildArg: BIFROST_PROVIDER_VERSION",
    f"provides: [\"pi@{PI_MIXIN_VERSION}\"]",
    "capabilities:",
    "  - type: com.docker.sandbox/network-policy@1",
    "    config:",
    "      runtime:",
    "        allow:",
    "          - registry.npmjs.org",
    "  - type: com.docker.sandbox/agent-context@1",
    "    config:",
    "      content: |",
    "        ## Pi",
    "",
    "        This sandbox carries Pi 1.5.0 and the pinned",
    f"        pi-bifrost-provider {BIFROST_PROVIDER_VERSION} extension as a project-owned mixin.",
    "        The CLI is installed in the image; run `pi` from the shell.",
    "",
    "        `pi update` and runtime package operations reach `registry.npmjs.org`,",
    "        which is allowed by this mixin. The `find` tool uses the bundled `fd`",
    "        binary, and the Bifrost provider discovers models at startup.",
    "  - type: com.docker.sandbox/agent-skills@1",
    "    optional: true",
    "    config:",
    "      path: /home/agent/.agents/skills",
]
PI_MIXIN_KIT_OUT.write_text("\n".join(pi_mixin_lines) + "\n")
shutil.copyfile(PI_MIXIN_DOCKERFILE, PI_MIXIN_OUT)

# The opinions mixin uses a Dockerfile for the vendored third-party skill.
OPINIONS_DOCKERFILE_OUT = ROOT / "sbx-kit-pifrost-opinions-chozian.dockerfile"

# The opinions mixin is optional and carries all repository files. Its package
# hook relies on htop, less, tmux, and vim from the selected Shell workload;
# those packages are verified but deliberately not reinstalled here.
opinion_lines = [
    "# syntax=docker/sandbox-kit:3",
    "# yaml-language-server: $schema=https://raw.githubusercontent.com/docker/sandbox-kit-spec/main/schema/kit.schema.json",
    "# Generated by scripts/render-kit-set.py from files/ and optional host Pi config.",
    "schemaVersion: \"3\"",
    "displayName: SBX Kit pifrost opinions (chozian)",
    "author: \"chozian\"",
    "description: >-",
    "  Optional chozian shell, editor, and Pi configuration for the Pifrost",
    "  workload, including the pinned Simple English writing skill.",
    "kind: mixin",
    f"dockerfile: {OPINIONS_DOCKERFILE_OUT.name}",
    f"version: \"{OPINIONS_VERSION}\"",
    "capabilities:",
    "  - type: com.docker.sandbox/agent-context@1",
    "    config:",
    "      content: |",
    *yaml_block(OPINIONS_CONTEXT, indent="        "),
    "",
    "  # Expose the image-bundled skill through the Pi discovery directory.",
    "  - type: com.docker.sandbox/agent-skill@1",
    "    name: Simple English",
    "    config:",
    f"      path: {SIMPLE_ENGLISH_BUNDLE_PATH}",
    "      name: simple-english",
    "",
    "  # The package hook is create-time and uses the selected workload's",
    "  # Debian package sources. Base-provided tools are not reinstalled.",
    "  - type: com.docker.sandbox/network-policy@1",
    "    config:",
    "      install:",
    "        allow:",
    "          - deb.debian.org",
    "          - dhi.io",
    "",
    "  - type: com.docker.sandbox/lifecycle@1",
    "    config:",
    "      install:",
    "        - user: \"0\"",
    "          description: Install chozian shell conveniences and restore Vim command aliases",
    "          command: >-",
    "            set -eu; mkdir -p /home/agent/.pi/agent;",
    "            chown -R agent:agent /home/agent/.pi; apt-get",
    "            update -qq; DEBIAN_FRONTEND=noninteractive apt-get install -y",
    "            --no-install-recommends bash-completion vim-solarized;",
    "            update-alternatives --install /usr/bin/vi vi /usr/bin/vim.basic 30;",
    "            update-alternatives --install /usr/bin/vim vim /usr/bin/vim.basic 30;",
    "            update-alternatives --install /usr/bin/view view /usr/bin/vim.basic 30;",
    "            apt-get clean; rm -rf /var/lib/apt/lists/*;",
    "            command -v htop; command -v less; command -v tmux; command -v vim;",
    "            command -v vi; command -v view;",
    "            test \"$(readlink -f /usr/bin/vi)\" = /usr/bin/vim.basic;",
    "            test \"$(readlink -f /usr/bin/vim)\" = /usr/bin/vim.basic;",
    "            test \"$(readlink -f /usr/bin/view)\" = /usr/bin/vim.basic;",
    "            test -f /usr/share/bash-completion/bash_completion;",
    "            command -v python; python --version",
    "      files:",
]

for path, source, mode, description in OPINION_FILES:
    opinion_lines.extend(file_entry(path, source, mode, description))

OPINIONS_OUT.write_text("\n".join(opinion_lines) + "\n")

opinions_dockerfile_lines = [
    "# syntax=docker/dockerfile:1",
    "# Generated by scripts/render-kit-set.py from vendor/simple-english/.",
    "FROM scratch",
    "COPY vendor/simple-english/skills/simple-english/ "
    f"{SIMPLE_ENGLISH_BUNDLE_PATH}/",
    f"COPY vendor/simple-english/LICENSE {SIMPLE_ENGLISH_BUNDLE_PATH}/LICENSE",
    f"COPY vendor/simple-english/SOURCE.txt {SIMPLE_ENGLISH_BUNDLE_PATH}/SOURCE.txt",
]
OPINIONS_DOCKERFILE_OUT.write_text("\n".join(opinions_dockerfile_lines) + "\n")

# The Shell + Pi set has no local workload Dockerfile: its content is the
# published shell workload plus the project-owned Pi mixin. The local files and
# lifecycle declarations above are merged as set contributions.

# DoD trust is deliberately a separate, opt-in mixin. The certificate files
# are content in its Dockerfile layer rather than large lifecycle file bodies.
dod_lines = [
    "# syntax=docker/sandbox-kit:3",
    "# yaml-language-server: $schema=https://raw.githubusercontent.com/docker/sandbox-kit-spec/main/schema/kit.schema.json",
    "# Generated by scripts/render-kit-set.py from certificates/.",
    "schemaVersion: \"3\"",
    "displayName: SBX Kit DoD CA certificates",
    "author: \"chozian\"",
    "description: >-",
    "  Optional DoD and approved host CA certificates for environments that",
    "  need to connect to DoD-protected services.",
    "kind: mixin",
    f"version: \"{DOD_VERSION}\"",
    "dockerfile: sbx-kit-pifrost-certs-dod.dockerfile",
    "",
    "# This mixin assumes the selected shell workload provides",
    "# update-ca-certificates. It does not add an apt hook: distro package",
    "# installation belongs to the selected workload.",
    "capabilities:",
    "  - type: com.docker.sandbox/lifecycle@1",
    "    config:",
    "      startup:",
    "        - user: \"0\"",
    "          description: Rebuild the system trust store from the optional DoD certificates",
    "          command: update-ca-certificates",
]

DOD_CERT_OUT.write_text("\n".join(dod_lines) + "\n")

# Keep the certificate bytes in an image layer, not in the manifest descriptor.
# The checked-in certificate files already use mode 0644. Do not use
# COPY --chmod here because BuildKit can apply that mode to intermediate
# directories, which prevents the agent user from traversing /usr/local.
dockerfile_lines = [
    "# syntax=docker/dockerfile:1",
    "# Generated by scripts/render-kit-set.py from certificates/.",
    "FROM scratch",
]
dockerfile_lines.extend(
    f"COPY certificates/{name} /usr/local/share/ca-certificates/{name}"
    for name in CERTIFICATES
)
DOD_DOCKERFILE_OUT.write_text("\n".join(dockerfile_lines) + "\n")

print(OUT)
print(OPINIONS_OUT)
print(DOD_CERT_OUT)
print(DOD_DOCKERFILE_OUT)
