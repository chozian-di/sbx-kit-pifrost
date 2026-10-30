#!/usr/bin/env python3
"""Render the Pifrost workload and optional DoD-certificate mixin.

The v3 descriptor cannot refer to local files for lifecycle file bodies, so
this script keeps the source files reviewable and embeds Pifrost's exact file
contents in the descriptor consumed by Docker Buildx. The workload Dockerfile
copies Pi's payload onto Docker's shell workload while deliberately keeping the
shell and Pi guidance out of the composed descriptor: older Docker Sandboxes
accept only one selected agent-context body. The script also generates a
companion Dockerfile so DoD certificate bytes live in the optional mixin's
image layer rather than inflating its manifest descriptor. Pi's models,
settings, and theme files use checked-in snapshots by default; host config is
an explicit opt-in.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sbx-kit-pifrost.yaml"
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


FILES = [
    ("/etc/sandbox-persistent.sh", ROOT / "files/sandbox-persistent.sh", "0644", "Persistent shell environment"),
    ("/home/agent/.bashrc", ROOT / "files/.bashrc", "0644", "Bash configuration"),
    ("/home/agent/.bash_aliases", ROOT / "files/.bash_aliases", "0644", "Bash aliases"),
    ("/home/agent/.dircolors", ROOT / "files/.dircolors", "0644", "Dircolors"),
    ("/home/agent/.pi/agent/models.json", pi_config_source("models.json"), "0644", "Pi model configuration"),
    ("/home/agent/.pi/agent/settings.json", pi_config_source("settings.json"), "0644", "Pi settings"),
    (
        "/home/agent/.pi/agent/themes/solarized-dark.json",
        pi_config_source("themes/solarized-dark.json"),
        "0644",
        "Pi Solarized Dark theme",
    ),
]

CERTIFICATES = (
    "5301-PA5260-Core.ds.amrdec.army.mil.crt",
    "DoD_v5.14.crt",
)
DOD_CERT_OUT = ROOT / "sbx-kit-pifrost-dod-certs.yaml"
DOD_DOCKERFILE_OUT = ROOT / "sbx-kit-pifrost-dod-certs.dockerfile"
WORKLOAD_DOCKERFILE_OUT = ROOT / "sbx-kit-pifrost.dockerfile"

WORKLOAD_VERSION = "1.0.0"
SHELL_REF = "docker.io/docker/sbx-kit-shell:1.0.0"
PI_REF = "docker.io/docker/sbx-kit-pi-mixin:0.86.1"
PI_VERSION = "0.86.1"

# These are the network entries in Docker Sandboxes v0.50.1's bundled local
# policy. The ai-services group is deliberately excluded from the allow set
# below and is denied explicitly. Keep this snapshot synchronized when the
# bundled local policy changes in a newer Sandbox release.
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
DEFAULT_LOCAL_POLICY_AI_SERVICES_DENY = DEFAULT_LOCAL_POLICY_ALLOW_GROUPS.pop(
    "default-ai-services"
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


# The runtime must receive one body for the legacy @1 capability. The
# published shell and Pi mixin each carry their own context declaration, and
# older sbx releases reject that pair before they can start the sandbox.
AGENT_CONTEXT = """This sandbox is Pifrost: a shell workload with Pi installed.

The shell provides bash, git, apt, Docker (compose/buildx), curl, gh, jq, make,
gcc, Python, Node/npm, tmux, vim, and htop. Install additional packages with
apt when needed.

Run `pi` to start the Pi coding agent. Pi uses the host-local Bifrost endpoint
configured by this kit. Its Bifrost credential is supplied through a host-side
custom secret; do not print, copy, or reconfigure the sentinel value. The
optional DoD certificate mixin adds only the approved certificates requested at
sandbox creation.

The sandbox's workspace is the project directory supplied to `sbx run`. Keep
changes inside that workspace unless the user explicitly asks otherwise.
"""


lines = [
    "# syntax=docker/sandbox-kit:3",
    "# yaml-language-server: $schema=https://raw.githubusercontent.com/docker/sandbox-kit-spec/main/schema/kit.schema.json",
    "# Generated by scripts/render-kit-set.py from files/ and optional host Pi config.",
    "schemaVersion: \"3\"",
    "displayName: SBX Kit Pifrost",
    "author: \"chozian\"",
    "description: >-",
    "  A reproducible Docker Sandbox workload based on Docker's shell image",
    "  with Pi, a specific shell, Pi and package configuration, tmux, and a",
    "  protected Bifrost connection. DoD trust material is supplied separately",
    "  by the opt-in certificate mixin.",
    "licenses: [MIT]",
    "kind: workload",
    f"version: \"{WORKLOAD_VERSION}\"",
    f"provides: [\"pi@{PI_VERSION}\"]",
    "dockerfile: sbx-kit-pifrost.dockerfile",
    "",
    "# Pifrost is built as one workload rather than a set of shell + Pi kits.",
    "# Those upstream images each expose agent context; older sbx runtimes",
    "# reject the resulting two @1 context files. The Dockerfile still layers",
    "# the upstream Pi payload onto the upstream shell filesystem.",
    "capabilities:",
    "  - type: com.docker.sandbox/sbx@1",
    "",
    "  # Keep exactly one context body for compatibility with legacy sbx @1.",
    "  - type: com.docker.sandbox/agent-context@1",
    "    config:",
    "      filename: AGENTS.md",
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
    "        - user: \"1000\"",
    "          description: Configure npm to use the sandbox proxy for Pi runtime installs",
    "          env: [HTTP_PROXY, HTTPS_PROXY]",
    "          command: >-",
    "            if [ -n \"${HTTP_PROXY:-}\" ]; then npm config set proxy=\"$HTTP_PROXY\"",
    "            https-proxy=\"${HTTPS_PROXY:-$HTTP_PROXY}\"; fi",
    "        - user: \"0\"",
    "          description: Install Bash completion, fd-find, and a Git pager; restore Vim command aliases",
    "          command: >-",
    "            set -eu; mkdir -p /home/agent/.pi/agent/themes;",
    "            chown -R agent:agent /home/agent/.pi; apt-get",
    "            update -qq; DEBIAN_FRONTEND=noninteractive apt-get install -y",
    "            --no-install-recommends bash-completion fd-find less;",
    "            update-alternatives --install /usr/bin/pager pager /usr/bin/less 100;",
    "            update-alternatives --set pager /usr/bin/less;",
    "            update-alternatives --install /usr/bin/vi vi /usr/bin/vim.basic 30;",
    "            update-alternatives --install /usr/bin/vim vim /usr/bin/vim.basic 30;",
    "            apt-get clean; rm -rf /var/lib/apt/lists/*; command -v less; command -v pager; test \"$(readlink -f /usr/bin/pager)\" = /usr/bin/less; command -v vi; command -v vim;",
    "            command -v python; python --version",
    "      files:",
])

for path, source, mode, description in FILES:
    lines.extend(file_entry(path, source, mode, description))

OUT.write_text("\n".join(lines) + "\n")

# The published workload owns the shell and Pi content in one Dockerfile, but
# only the workload descriptor above is exposed to sbx. In particular, do not
# copy Pi's staged context file into the descriptor: the single inline body
# above is the compatibility boundary for older runtimes.
workload_dockerfile_lines = [
    "# syntax=docker/dockerfile:1.7",
    "# Generated by scripts/render-kit-set.py from the published workload refs.",
    f"FROM {PI_REF} AS pi",
    f"FROM {SHELL_REF}",
    "COPY --from=pi /usr/local/share/npm-global /usr/local/share/npm-global",
    "COPY --from=pi /usr/local/bin/pi /usr/local/bin/pi",
]
WORKLOAD_DOCKERFILE_OUT.write_text("\n".join(workload_dockerfile_lines) + "\n")

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
    "version: \"1.0.0\"",
    "dockerfile: sbx-kit-pifrost-dod-certs.dockerfile",
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
# COPY --chmod also normalizes the source mode on filesystems that expose all
# checkout files as executable.
dockerfile_lines = [
    "# syntax=docker/dockerfile:1",
    "# Generated by scripts/render-kit-set.py from certificates/.",
    "FROM scratch",
    "# Seed the parent directory with traverse permissions; the second copy",
    "# below normalizes the certificate itself to non-executable 0644.",
    f"COPY --chmod=0755 certificates/{CERTIFICATES[0]} /usr/local/share/ca-certificates/{CERTIFICATES[0]}",
]
dockerfile_lines.extend(
    f"COPY --chmod=0644 certificates/{name} /usr/local/share/ca-certificates/{name}"
    for name in CERTIFICATES
)
DOD_DOCKERFILE_OUT.write_text("\n".join(dockerfile_lines) + "\n")

print(OUT)
print(DOD_CERT_OUT)
print(DOD_DOCKERFILE_OUT)
