# SBX Kit Pifrost

SBX Kit Pifrost is a Docker Sandbox kit. A kit is a package that creates a
configured sandbox. Pifrost sends model requests through a Bifrost gateway.

A workload provides the main sandbox environment. A mixin adds files or tools
to that environment. Pifrost uses Docker's published Shell workload and a
project-owned Pi mixin:

- [`docker.io/sbx/shell:1.0.3`](https://hub.docker.com/r/sbx/shell) is a
  Debian-based shell workload. It includes Bash, Git, `apt`, Docker, Compose,
  Buildx, Node.js, npm, Python, and common command-line tools.
- [`docker.io/choziandi/sbx-kit-pifrost-pi-mixin:1.5.0`](https://hub.docker.com/r/choziandi/sbx-kit-pifrost-pi-mixin) is the project-owned
  Pi 1.5.0 mixin. It includes Debian's recommended `fd-find` binary, an npm
  proxy hook, and the pinned
  [`pi-bifrost-provider`](https://github.com/lxdlam/pi-bifrost-provider)
  extension.

The Pifrost kit adds Bifrost network policy, Bifrost lifecycle configuration,
and host credential instructions. The optional
`sbx-kit-pifrost-opinions-chozian` mixin adds chozian's reviewed shell files
and the current Pi settings snapshot.
DoD trust certificates are available in a separate, optional mixin.

The published artifact name is:

```text
docker.io/choziandi/sbx-kit-pifrost:1.0.0
```

## Requirements

Use the first sections to install and run the published kit. Use the later
sections to build, test, or publish a customized kit.

- A WSL2 Ubuntu 24.04 or newer distribution when using local Sandboxes.
- Docker Sandboxes and the Linux `sbx` CLI installed inside WSL Ubuntu.
- Nested virtualization and KVM access for local Sandboxes.
- An OpenAI-compatible Bifrost gateway reachable at port `8080`.
- A Bifrost virtual key.
- A Docker Hub account authorized for the Sandboxes registry session.
- A GitHub account and GitHub CLI only if GitHub access is needed inside the
  sandbox.

Cloud Sandboxes do not require local WSL KVM.

## 1. Prepare WSL KVM and install Docker Sandboxes

A local Docker Sandbox workload runs in a virtual machine (VM). WSL2 must
therefore use nested virtualization, load a KVM module, and provide access to
`/dev/kvm`. Nested virtualization lets a VM run inside another VM.

Check the Ubuntu release and KVM state:

```bash
. /etc/os-release && printf '%s\n' "$PRETTY_NAME"
lsmod | grep kvm
ls -l /dev/kvm
```

A working setup loads a KVM module. The WSL user must be able to read and
write `/dev/kvm`. Add the user to the KVM group and start a new shell:

```bash
sudo usermod -aG kvm "$USER"
newgrp kvm
test -r /dev/kvm && test -w /dev/kvm && echo "/dev/kvm is accessible"
```

If `/dev/kvm` is absent or inaccessible, fix WSL nested virtualization before
continuing. Enable hardware virtualization on the physical host or expose KVM
through an outer VM as needed.

Install the `docker-sbx` package from Docker's APT repository:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt-get update
sudo apt-get install -y docker-sbx
```

Make sure that the installation works:

```bash
sbx version
```

The Docker Engine and Docker Desktop are not required for this WSL
installation step. Docker Sandboxes provides the Docker environment inside the
sandbox.

Disable Docker Sandboxes CLI usage telemetry for interactive WSL shells. The
wrapper uses the Linux `sbx` executable directly and avoids recursively
invoking the wrapper:

```bash
cat >> ~/.bash_aliases <<'EOF'
# Disable Docker Sandboxes CLI usage telemetry.
alias sbx='SBX_NO_TELEMETRY=1 command sbx'
EOF
source ~/.bash_aliases
```

For non-interactive commands, set `SBX_NO_TELEMETRY=1` in the command's
environment instead of relying on the interactive alias.

### Why Docker Sandboxes run in WSL Ubuntu

Install and invoke the Linux `sbx` CLI inside WSL Ubuntu. A client outside
WSL must translate the WSL workspace into a host mount. This translation can
produce I/O and xattr errors when BuildKit accesses files. Run `sbx` from WSL
and pass a native `/home/...` path to avoid this translation. Keep project
checkouts on WSL's Linux filesystem instead of `/mnt/...` when possible.

A local Sandbox VM runs inside WSL2. WSL therefore needs nested virtualization,
a loaded KVM module, access to `/dev/kvm`, and the WSL user in the `kvm` group.
WSL's memory and disk limits also apply to the nested runtime. Increase these
limits if the sandbox or its build workload needs more resources. Cloud
Sandboxes do not need local WSL KVM.

### First-use network policy

When Docker Sandboxes asks for an initial network policy, start with a policy
that denies all network access. The Pifrost kit adds the endpoints that it
needs. If a request is denied, review the active policy before allowing another
endpoint:

```bash
sbx policy ls --wide
sbx policy log
```

### Enable host-side `sbx` Bash completion

This completion is for the WSL/host `sbx` command. It is separate from Bash
completion inside the sandbox:

```bash
sudo apt-get install -y bash-completion
sbx completion bash | sudo tee /etc/bash_completion.d/sbx >/dev/null
```

Start a new WSL shell to load the completion. To load it in the current shell:

```bash
source /usr/share/bash-completion/bash_completion
```

Regenerate the completion file after upgrading the `docker-sbx` package.

## 2. Start and test Bifrost

Pifrost expects Bifrost at:

```text
Host:     http://localhost:8080
Sandbox:  http://host.docker.internal:8080/v1
```

For the upstream Maxim Bifrost gateway, install Node.js 24 or newer and the
CLI using the approved installation method:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
npm --version
npm install --global @maximhq/bifrost
bifrost --host localhost --port 8080
```

Run Bifrost in one WSL terminal. Use another WSL terminal for the remaining
setup. Configure the approved upstream provider and model in Bifrost. Create a
Bifrost virtual key. For reference, see Bifrost's official [gateway setup
guide](https://docs.getbifrost.ai/quickstart/gateway/setting-up), [provider
configuration guide](https://docs.getbifrost.ai/quickstart/gateway/provider-configuration),
and [virtual keys documentation](https://docs.getbifrost.ai/features/governance/virtual-keys).
The upstream Bifrost project is also available on [GitHub](https://github.com/maximhq/bifrost).

Keep the real key on the host and test the gateway:

```bash
read -rsp 'Bifrost API key: ' BIFROST_API_KEY
echo
export BIFROST_API_KEY

curl --fail http://localhost:8080/health
curl --fail http://localhost:8080/v1/models \
    -H "Authorization: Bearer $BIFROST_API_KEY"
```

## 3. Make GitHub available (optional)

Skip this section if the sandbox will not use GitHub. Otherwise install and
authenticate the GitHub CLI in WSL Ubuntu. Homebrew's Linux prefix is one
supported option:

```bash
sudo apt-get update
sudo apt-get install -y build-essential procps curl file git
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
brew install gh
gh auth login
gh auth status
```

If `gh` is installed through `apt` or the official GitHub CLI repository,
make sure that it is on `PATH`. Run the same authentication commands.

Register the host-side token command with Docker Sandboxes:

```console
sbx secret set github --command 'gh auth token'
```

The credential proxy is a host service that supplies credentials when a
command needs them. It runs `gh auth token` on the host. The real GitHub token
is not copied into the repository or sandbox.

## 4. Authenticate Docker Sandboxes

From the WSL Ubuntu shell, authenticate the Sandboxes registry session:

```console
sbx login
```

Do not run `docker login` inside the sandbox or pass a Docker Hub token with
`sbx run -e`. Host-side Sandboxes authentication keeps registry credentials out
of the sandbox.

## 5. Register the protected Bifrost key

Run this in the host/WSL shell where the real key is loaded:

```console
sbx secret set-custom \
    --host host.docker.internal \
    --host localhost \
    --env BIFROST_API_KEY \
    --value "$BIFROST_API_KEY"
```

The two hosts are intentional. Pi calls `host.docker.internal:8080` from the
sandbox. The host-side credential route uses `localhost:8080`. These hosts are
credential matching targets. They are not two Pi endpoints.

List the registered secret:

```console
sbx secret ls
```

If Bifrost rotates the key, rerun `sbx secret set-custom` with the new value.
Never put the key in `files/settings.json`, the generated YAML, or a normal
`sbx run -e` environment variable.

## 6. Create and use a Pifrost sandbox

For a project workspace, pass a native WSL path. Keep the checkout on the WSL
Linux filesystem, such as `/home/<user>/git/<project>`, instead of a translated
path such as `/mnt/c/...` when possible:

```console
sbx run docker.io/choziandi/sbx-kit-pifrost:1.0.0 \
    "/home/<user>/git/<project>" \
    --name pifrost
```

Prefer mapping one project rather than a parent directory:

```console
sbx run docker.io/choziandi/sbx-kit-pifrost:1.0.0 \
    "/home/<user>/git/project-a" \
    --name pifrost-project-a
```

This limits direct read/write access to the intended project. Mapping multiple
projects is possible but gives the sandbox access to all of them:

```console
sbx run docker.io/choziandi/sbx-kit-pifrost:1.0.0 \
    "/home/<user>/git" \
    --name pifrost-all-projects
```

The core artifact provides the Shell/Pi workload, Bifrost route, credential
policy, and Python 3 compatibility command. The artifact is the built package
that you run as a sandbox. The current chozian Pi and shell profile is optional.
The opinionated mixin section below describes it.

After leaving the sandbox, reenter an existing named sandbox with:

```console
sbx run --name pifrost
```

Inside the sandbox, start Pi with:

```bash
pi
```

The request path is:

```text
Pi in sandbox
  -> host.docker.internal:8080
  -> Docker Sandboxes network and credential proxy service
  -> localhost:8080
  -> Bifrost in WSL
```

## Optional DoD certificate mixin

The Pifrost workload does not include DoD or host-specific trust roots by
default. If your environment requires the published certificate mixin, use it
when creating a Pifrost sandbox:

```console
sbx run docker.io/choziandi/sbx-kit-pifrost:1.0.0 \
    "/home/<user>/git/<project>" \
    --kit docker.io/choziandi/sbx-kit-pifrost-certs-dod:1.0.0 \
    --name pifrost
```

Select the mixin only where the checked-in DoD/host roots are approved and
required.

## Optional chozian opinionated mixin

The core Pifrost artifact contains the Shell/Pi workload, Bifrost routing,
credential policy, and the core `python-is-python3` compatibility package. The
optional opinions mixin contains the reviewed shell/editor files and
chozian's current Pi settings profile.

The mixin installs only packages that the selected Shell workload does not
already provide:

- `bash-completion`
- `vim-solarized`
- Vim command alternatives for `/usr/bin/vi`, `/usr/bin/vim`, and
  `/usr/bin/view` (read-only Vim)

The core artifact installs `python-is-python3`, which provides the unversioned
`python` command as the Python 3 compatibility command. The Shell workload
already provides `htop`, `less`, `tmux`, and `vim`. The opinions mixin checks
those tools but does not reinstall them.

The published opinions mixin adds the reviewed chozian shell/editor profile
and Pi settings. Select it only when that profile is wanted. Bifrost models
and capabilities are discovered dynamically by the bundled provider extension:

```console
sbx run docker.io/choziandi/sbx-kit-pifrost:1.0.0 \
    "/home/<user>/git/<project>" \
    --kit docker.io/choziandi/sbx-kit-pifrost-opinions-chozian:1.0.0 \
    --name pifrost
```

Use both optional mixins when the sandbox needs the current chozian profile and
approved DoD trust roots:

```console
sbx run docker.io/choziandi/sbx-kit-pifrost:1.0.0 \
    "/home/<user>/git/<project>" \
    --kit docker.io/choziandi/sbx-kit-pifrost-opinions-chozian:1.0.0 \
    --kit docker.io/choziandi/sbx-kit-pifrost-certs-dod:1.0.0 \
    --name pifrost
```

## Security and network behavior

The local network policy blocks direct AI-provider access by default. It
allows the host Bifrost route and the package and runtime endpoints that the
shell and Pi need. The bundled `default-ai-services` group is denied except for
`models.dev:443`, which Pi uses for runtime model metadata. Direct OpenAI,
Anthropic, Gemini, Perplexity, Cursor, and related provider routes remain
blocked. Bifrost is the intended model path.

The host-side custom secret remains outside the sandbox. Pifrost uses Bifrost
for provider access rather than connecting directly to AI-provider endpoints.

Use the effective-policy tools when troubleshooting:

```console
sbx policy ls --wide
sbx policy log
```

A host/global policy or organization policy can still restrict a kit's network
access.

## Development and customization

The rest of this README is for maintainers and users who build a private or
customized variant. End users can use the published artifacts and setup
instructions above. They do not need to render or build this repository.

### Architecture

`sbx-kit-pifrost.yaml` is a formal `kind: set` descriptor. A capability is a
set feature that adds behavior, such as a network policy or lifecycle rule.
The descriptor contains one published workload, one published mixin, and local
set capabilities:

```text
source set
  ├── sbx/shell       (kind: workload)
  ├── choziandi/sbx-kit-pifrost-pi-mixin (kind: mixin)
  └── local Pifrost policy and lifecycle capabilities

optional mixins
  ├── sbx-kit-pifrost-opinions-chozian
  └── sbx-kit-pifrost-certs-dod

published result     (kind: workload)
```

The Shell workload owns the root filesystem and launch command. The launch
command is the command that starts the workload. The project-owned Pi mixin
adds Pi 1.5.0 and the Bifrost provider extension. It does not replace the
shell entrypoint, which is the command that starts the shell. The mixin is
derived from Docker's published
[`sbx/pi-mixin`](https://hub.docker.com/r/sbx/pi-mixin) recipe. The local
capabilities add the Pifrost network policy, lifecycle configuration, and
persistent Bifrost URL. The optional mixins add chozian's Pi and shell profile
and approved DoD trust roots when selected.

The source descriptor uses readable version tags. A manifest digest is a
unique identifier for one published image version. Publishing resolves each
reference to a manifest digest:

```yaml
kind: set
kits:
  - ref: docker.io/sbx/shell:1.0.3
  - ref: docker.io/choziandi/sbx-kit-pifrost-pi-mixin:1.5.0
```

### Opinions mixin customization

The opinions mixin supplies these reviewed files:

- `vendor/simple-english/` for the pinned Simple English Pi skill and its
  supporting references. The generated mixin declares it with
  `com.docker.sandbox/agent-skill@1` and stores the bundle outside
  `/home/agent/.agents/skills`. Docker Sandbox exposes it in that discovery
  directory when it creates the sandbox.
- `files/.bashrc`, `files/.bash_aliases`, and `files/.dircolors` for the
  interactive shell presentation and aliases.
- `files/.vimrc` for the Solarized Dark Vim colorscheme.
- `files/sandbox-persistent.sh` for the persistent shell/editor environment.
- `files/settings.json` for general Pi behavior and terminal preferences.

The source snapshots are used by default for a reviewable build. To explicitly
use matching files from the current host Pi configuration:

```console
python3 scripts/render-kit-set.py --use-host-pi-config
```

The matching host file is `~/.pi/agent/settings.json`. Review host-derived
changes before publishing. For a fully reviewable release, copy the intended
host version into `files/settings.json` and render without the flag.

Build and publish the opinions mixin as its own artifact. This release uses
version `1.0.0`. The artifact includes the pinned Simple English skill.

If you change the mixin contents for a new release, update the version in
`scripts/render-kit-set.py`, regenerate the descriptors, and update the image
references in this README.

```console
docker buildx build . \
    -f ./sbx-kit-pifrost-opinions-chozian.yaml \
    -t docker.io/choziandi/sbx-kit-pifrost-opinions-chozian:1.0.0 \
    --push
```

### Source files

- `certificates/` contains the optional DoD/host trust certificate snapshot.
- `vendor/simple-english/` contains the pinned [Simple English skill](https://github.com/AminBlg/SimpleEnglish)
  imported from AminBlg/SimpleEnglish version 2.1.1. `SOURCE.txt` records the
  exact upstream commit.
- `scripts/render-kit-set.py` renders the Pifrost set, the optional chozian
  opinions mixin, and the certificate mixin.
- `sbx-kit-pifrost.yaml`, `sbx-kit-pifrost-pi-mixin.yaml`,
  `sbx-kit-pifrost-pi-mixin.dockerfile`,
  `sbx-kit-pifrost-opinions-chozian.yaml`, `sbx-kit-pifrost-certs-dod.yaml`,
  and `sbx-kit-pifrost-certs-dod.dockerfile` are generated output. Do not edit
  them by hand. The Pi mixin Dockerfile template is
  `templates/pifrost-pi-mixin.dockerfile`.

## Render, validate, build, and publish

After changing a source file:

```console
python3 scripts/render-kit-set.py
bash scripts/validate-python.sh
git diff -- files certificates scripts \
    sbx-kit-pifrost.yaml \
    sbx-kit-pifrost-opinions-chozian.yaml \
    sbx-kit-pifrost-certs-dod.yaml \
    sbx-kit-pifrost-certs-dod.dockerfile
```

Validate the Pifrost set with Docker Buildx:

```console
docker buildx build . \
    -f ./sbx-kit-pifrost.yaml \
    -t sbx-kit-pifrost:1.0.0 \
    --provenance=false \
    --output type=oci,dest=/tmp/sbx-kit-pifrost.oci.tar
```

Validate the project-owned Pi mixin separately:

```console
docker buildx build . \
    -f ./sbx-kit-pifrost-pi-mixin.yaml \
    -t sbx-kit-pifrost-pi-mixin:1.5.0 \
    --provenance=false \
    --output type=oci,dest=/tmp/sbx-kit-pifrost-pi-mixin.oci.tar
```

Publish the project-owned Pi mixin before publishing the set:

```console
docker buildx build . \
    -f ./sbx-kit-pifrost-pi-mixin.yaml \
    -t docker.io/choziandi/sbx-kit-pifrost-pi-mixin:1.5.0 \
    --push
```

Validate the opinions mixin separately:

```console
docker buildx build . \
    -f ./sbx-kit-pifrost-opinions-chozian.yaml \
    -t sbx-kit-pifrost-opinions-chozian:1.0.0 \
    --provenance=false \
    --output type=oci,dest=/tmp/sbx-kit-pifrost-opinions-chozian.oci.tar
```

Validate the certificate mixin separately:

```console
docker buildx build . \
    -f ./sbx-kit-pifrost-certs-dod.yaml \
    -t sbx-kit-pifrost-certs-dod:1.0.0 \
    --provenance=false \
    --output type=oci,dest=/tmp/sbx-kit-pifrost-certs-dod.oci.tar
```

Publish the Pifrost set under its canonical Docker Hub namespace:

```console
docker buildx build . \
    -f ./sbx-kit-pifrost.yaml \
    -t docker.io/choziandi/sbx-kit-pifrost:1.0.0 \
    --push
```

Publish the certificate mixin only if it is needed:

```console
docker buildx build . \
    -f ./sbx-kit-pifrost-certs-dod.yaml \
    -t docker.io/choziandi/sbx-kit-pifrost-certs-dod:1.0.0 \
    --push
```

Verify published manifests:

```console
docker buildx imagetools inspect \
    docker.io/choziandi/sbx-kit-pifrost:1.0.0
docker buildx imagetools inspect \
    docker.io/choziandi/sbx-kit-pifrost-opinions-chozian:1.0.0
docker buildx imagetools inspect \
    docker.io/choziandi/sbx-kit-pifrost-certs-dod:1.0.0
```

The source references use version-pinned tags. The published set records
resolved kit digests. Pin those digests explicitly in a controlled release
process when byte-for-byte reproducibility is required.

## Testing checklist

Run these end-to-end tests from a WSL Ubuntu host with KVM and nested
virtualization. You can also run them from Docker Cloud Sandboxes:

- Test Bifrost health, `/v1/models`, and credential registration.
- Run `python --version` and `git log` in a core-only sandbox.
- Test `vim`, `tmux`, `htop`, `less`, shell aliases, and Pi requests with the
  optional opinions mixin.
- Test dynamic Pi Bifrost model discovery and `models-store.json` with the
  opinions mixin.
- Run `pi update` and test runtime npm access.
- Review the effective local and organization network policies.
- Test DoD-trusted TLS when the optional certificate mixin is selected. Repeat
  the test when the certificate mixin is combined with the opinions mixin.

## License

MIT
