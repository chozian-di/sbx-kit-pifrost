# SBX Kit Pifrost

SBX Kit Pifrost is a reproducible Docker Sandboxes v3 workload for running the
Pi coding agent in an isolated shell. It is based on Docker's shell workload
and carries the Pi payload in one workload descriptor, alongside Python,
`vim`, `tmux`, `htop`, a Git pager, Bash programmable completion, Pi
configuration, and a protected connection to an OpenAI-compatible Bifrost
gateway. DoD trust
certificates are kept in a separate opt-in mixin because they are not relevant
to most users.

The quickest way to use the published kit is below. Customization and
maintainer instructions are later in this README.

Command examples use `[tag]` and `[version]` placeholders. Replace these
placeholders with the tag or version you intend to use before running the
commands.

## Use the published kit

The published image is:

```text
docker.io/choziandi/sbx-kit-pifrost:1.0.0
```

A running sandbox gets the Pi configuration and tools from the kit. The
Bifrost key, GitHub token, and Docker Hub credentials stay on the host and are
provided through Docker Sandboxes' credential proxy when needed. The standard
Linux CA store is provided by the shell workload; DoD CA material is only
installed when the optional certificate mixin is selected.

### What you need

- A WSL2 Ubuntu 24.04 or newer distribution. The Docker Sandboxes CLI and
  local runtime must be installed and run inside WSL Ubuntu, not through a
  client running outside WSL.
- Nested virtualization exposed to WSL2, with KVM available at `/dev/kvm`. The
  WSL user running `sbx` must be a member of the `kvm` group.
- An OpenAI-compatible Bifrost gateway reachable on port `8080`.
- A Bifrost virtual key. Have the key available for initial registration, then
  let `sbx` store it as a static host-side secret. Do not put it in this
  repository or in Pi's `models.json`.
- A Docker Hub account authorized to use the kit. The published repository is
  public, but `sbx login` is still required for the Sandboxes Docker Hub
  session used by the shell workload.
- A GitHub account and the GitHub CLI only if you want GitHub access from the
  sandbox.

### 1. Prepare WSL KVM and install Docker Sandboxes

**First-use network policy recommendation:** When Docker Sandboxes first asks you
which network policy to use, select the policy that blocks everything by
default. This fail-closed baseline avoids unexpected outbound access; the kit
adds only the explicit endpoints it requires. If a request is denied, inspect
the effective rules with `sbx policy ls --wide` and `sbx policy log` before
loosening the policy.

Docker Sandboxes local workloads run a VM, so WSL2 must be able to provide
nested virtualization. Hardware virtualization must be enabled by the
physical host (and exposed through any outer VM), and `/dev/kvm` must be
usable by the WSL user. Check the Ubuntu release and KVM before installing:

```bash
. /etc/os-release && printf '%s\n' "$PRETTY_NAME"
lsmod | grep kvm
ls -l /dev/kvm
```

A working setup has a KVM module in the `lsmod` output and a readable and
writable `/dev/kvm`. Add the current WSL user to the KVM group, then start a
new shell so the group change is active:

```bash
sudo usermod -aG kvm "$USER"
newgrp kvm
test -r /dev/kvm && test -w /dev/kvm && echo "/dev/kvm is accessible"
```

If KVM is not loaded or `/dev/kvm` is absent, local Sandboxes cannot start.
Fix WSL's nested-virtualization support before continuing. Cloud Sandboxes do
not require local KVM.

Install the `docker-sbx` package from Docker's APT repository. This installs
the Sandboxes CLI and runtime in Ubuntu; Docker Desktop and a host Docker
Engine are not required for this step:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
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

Disable Docker Sandboxes CLI usage telemetry for interactive WSL shells. The
wrapper uses the Linux `sbx` executable directly and avoids recursively
invoking the wrapper:

```bash
cat >> ~/.bash_aliases <<'EOF'
# Disable Docker Sandboxes CLI usage telemetry.
alias sbx='SBX_NO_TELEMETRY=1 command sbx'
EOF
source ~/.bash_aliases
sbx --version
```

For non-interactive commands, set `SBX_NO_TELEMETRY=1` in the command's
environment instead of relying on the interactive alias.

### Enable Bash completion for `sbx`

Bash completion for the host/WSL `sbx` CLI is separate from the programmable
completion configured inside the sandbox. Install the Bash completion package,
then generate the `sbx` completion script in Bash's system completion
directory:

```bash
sudo apt-get install -y bash-completion
sbx completion bash | sudo tee /etc/bash_completion.d/sbx > /dev/null
```

Start a new WSL shell to load the completion. To load it in the current shell
instead, run:

```bash
source /usr/share/bash-completion/bash_completion
```

You can now type `sbx ` and press Tab to complete commands and options. If you
update the `docker-sbx` package, regenerate the installed script with the same
`sbx completion bash` command.

### 2. Start and check Bifrost

The kit expects an OpenAI-compatible Bifrost endpoint at
`http://localhost:8080` from the host and at
`http://host.docker.internal:8080/v1` from the sandbox. For the upstream Maxim
Bifrost gateway, install Node.js 24 or newer and the CLI in WSL Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
npm --version
npm install --global @maximhq/bifrost
bifrost --host 0.0.0.0 --port 8080
```

Run Bifrost in one WSL terminal and use another WSL terminal for the
remaining setup steps. Leave Bifrost running while using the sandbox. Open
<http://localhost:8080>, configure the approved upstream provider and model,
and create a Bifrost virtual key. If your organization supplies a private
Bifrost build, use its approved installation method while keeping the same
endpoint, port, and key requirements.

Keep the key in a host-side secret manager or environment variable. For the
checks and initial registration below, load it into the current WSL shell
without putting it in shell history:

```bash
read -rsp 'Bifrost API key: ' BIFROST_API_KEY
echo
export BIFROST_API_KEY

curl --fail http://localhost:8080/health
curl --fail http://localhost:8080/v1/models \
    -H "Authorization: Bearer $BIFROST_API_KEY"
```

The sandbox uses `host.docker.internal:8080`, not `localhost:8080`. If it
cannot reach Bifrost, verify that Bifrost is listening on `0.0.0.0:8080` in
WSL and that the effective Sandboxes network policy allows the host route.

### 3. Make GitHub available (optional)

Skip this step if the sandbox will not use GitHub. Otherwise install and
authenticate `gh` in WSL Ubuntu. The following commands use Homebrew's default
Linux prefix; if `gh` is installed another way, make sure it is on `PATH`:

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

Register the GitHub token command with the Linux `sbx` CLI:

```console
$ sbx secret set github --command 'gh auth token'
```

The credential proxy runs `gh auth token` as the current WSL user on demand;
the token is not copied into the repository or sandbox.

### 4. Authenticate Docker Sandboxes

From the WSL Ubuntu shell, run:

```console
$ sbx login
```

Use a Docker Hub account associated with the required corporate email. Do not
run `docker login` inside the sandbox or pass a Docker Hub token with
`sbx run -e`; `sbx login` keeps the credential on the host and authenticates
registry requests through the proxy.

### 5. Register the protected Bifrost key

Run this in the host/WSL shell where the real `BIFROST_API_KEY` is loaded:

```console
$ sbx secret set-custom \
    --host host.docker.internal \
    --host localhost \
    --env BIFROST_API_KEY \
    --value "$BIFROST_API_KEY"
```

The shell expands `$BIFROST_API_KEY` for this initial registration, but
`--value` stores the resulting value as a static custom secret. `sbx` does not
need the environment variable to be available later. The two `--host` flags
are intentional: the sandbox addresses Bifrost as `host.docker.internal:8080`,
while the host-side route is evaluated as `localhost:8080`. They are credential
matching targets, not two sandbox endpoints.

Confirm that the custom secret is registered:

```console
$ sbx secret ls
```

The output should include an entry similar to:

```text
(global)   host.docker.internal, localhost   BIFROST_API_KEY   ...
```

If Bifrost rotates the key, load the new value and rerun `sbx secret set-custom`
with the same hosts and `--value` option. Never pass the key with `sbx run -e`,
write it to Pi configuration, or commit it. The real value stays on the host;
inside the sandbox `BIFROST_API_KEY` is only a custom-secret sentinel. Remove
any stale `bifrost` service entry if one was previously registered; this
workload uses the custom binding.

### 6. Create and use the sandbox

For a project sandbox, choose its workspace when the sandbox is created. A
workspace used by the default direct-mount mode cannot be added or changed by
reattaching to an existing sandbox. The first path after the kit reference is
the primary workspace, and it is mounted read/write.

Because the Linux `sbx` CLI runs inside WSL, pass the native Linux path to a
WSL workspace. Keep the checkout on WSL's Linux filesystem, such as
`/home/[user_name]/git/[project_name]`, rather than on a translated or mounted
host filesystem such as `/mnt/c/...`:

```console
$ sbx run docker.io/choziandi/sbx-kit-pifrost:[tag] \
    "/home/[user_name]/git/[project_name]" \
    --name pifrost
```

Prefer mapping one project rather than a parent directory. This keeps the
contents of other projects outside the sandbox's direct workspace mount. For
example, map only `project-a`:

```console
$ sbx run docker.io/choziandi/sbx-kit-pifrost:[tag] \
    "/home/[user_name]/git/project-a" \
    --name pifrost-project-a
```

While not recommended, multiple projects can be mapped together by mounting
the home directory's `git` directory, if all of your Git checkouts are stored
there. This gives the sandbox direct read/write access to every checkout under
that directory, not just the project you intend to work on:

```console
$ sbx run docker.io/choziandi/sbx-kit-pifrost:[tag] \
    "/home/[user_name]/git" \
    --name pifrost-all-projects
```

If this sandbox must reach DoD-protected services, add the separate
certificate mixin at create time. It is intentionally not included in the
Pifrost workload by default:

```console
$ sbx run docker.io/choziandi/sbx-kit-pifrost:[tag] \
    --kit docker.io/choziandi/sbx-kit-pifrost-dod-certs:1.0.0 \
    --name pifrost
```

Use the same `--kit` option when composing a customized local or published
workload. Select the certificate mixin only for environments where these
specific DoD/host roots are approved and required.

After leaving the sandbox, reenter the existing named sandbox without
recreating it:

```console
$ sbx run --name pifrost
```

Inside the sandbox, Pi is ready to use and the kit's tools can be checked with:

```bash
pi
python --version
vim --version
tmux -V
htop
```

When Pi sends a model request, it uses the Bifrost provider configured in the
kit. Pi sends its normal `Authorization` header with the custom-secret sentinel;
the credential proxy substitutes the real key only for the matching host
request. The real key is not stored in the sandbox filesystem or exposed as a
normal sandbox environment variable.

### Everyday checklist

1. Start Bifrost on the host and verify its health endpoint.
2. Use the static Bifrost key stored by `sbx`; rerun `sbx secret set-custom` if
   the key rotates.
3. Start or enter the named sandbox with `sbx`.
4. Run `pi` and work normally.

If a request fails, check the host service and effective Sandboxes policy:

```console
$ curl --fail http://localhost:8080/health
$ sbx policy ls --wide
$ sbx policy log
```

A host/global `sbx policy` rule or organization policy can still restrict a
kit's network access.

## Security and network behavior

### Why Docker Sandboxes run in WSL Ubuntu

Install and invoke the Linux `sbx` CLI inside WSL Ubuntu rather than using a
client outside WSL. An outside client has to translate a WSL workspace into a
host-visible mount, which can produce I/O and xattr errors when BuildKit
accesses files on the WSL filesystem. Running `sbx` from WSL and passing a
native `/home/...` path avoids that client-side path translation.
Keep project checkouts on WSL's Linux filesystem instead of `/mnt/...` when
possible.

The tradeoff is that a local Sandbox VM runs nested inside WSL2. WSL therefore
needs nested virtualization, a loaded KVM module, access to `/dev/kvm`, and the
WSL operator in the `kvm` group. WSL's memory and disk limits also apply to the
nested runtime; increase them if the sandbox or its build workload needs more
resources. Cloud Sandboxes do not need local WSL KVM.

### Bifrost isolation

Bifrost is the single OpenAI-compatible control point between Pi and approved
upstream providers. Pi receives a Bifrost virtual key, not an OpenAI,
Anthropic, or other provider key. Upstream provider keys remain in Bifrost's
provider configuration.

The request path is:

```text
Pi in sandbox
  -> host.docker.internal:8080
  -> Docker Sandboxes network and credential proxy
  -> localhost:8080
  -> Bifrost in WSL
```

The kit's Pi configuration points to
`http://host.docker.internal:8080/v1`. The `localhost:8080` network allow covers
the host-side route used by the Sandboxes proxy; `localhost` is not a second Pi
endpoint.

Docker Sandboxes supplies a current proxy CA for each sandbox. This project
does not bundle that sandbox-specific CA. The Pifrost workload installs only
the standard CA package. The separate `sbx-kit-pifrost-dod-certs` mixin
copies the two checked-in DoD/host certificate snapshots as CA files and runs
`update-ca-certificates` at startup when explicitly selected.

### Network policy

The workload snapshots the network entries from Docker Sandboxes v0.50.1's
bundled local policy. It allows the bundled package-manager,
code-and-containers, cloud-infrastructure, OS-package, and
certificate-validation groups. It explicitly denies the bundled
`default-ai-services` group, including direct access to OpenAI, Anthropic,
Gemini, Perplexity, Cursor, and related services. Bifrost is the intended model
route.

The published workload is intentionally flattened instead of declaring the
shell and Pi images as a v3 `kits` set. Both upstream images expose an
`agent-context@1` capability; older Docker Sandbox runtimes reject the two
resulting context files before startup. `sbx-kit-pifrost.dockerfile` copies the
Pi payload onto the shell filesystem, while the Pifrost descriptor exposes one
combined inline context body.

`deb.debian.org` and `dhi.io` are install-phase allows for the lifecycle hook.
The package-manager defaults remain available at runtime for Pi extensions and
other runtime installs. A v3 network deny takes precedence over an included
kit's allow, and external host or organization policy cannot be removed by this
kit.

Bash programmable completion, `fd-find`, and `less` (the Git pager) are
installed from the shell workload's Debian package manager by a root create-time
lifecycle hook. The selected shell workload already supplies the CA store,
Python, `htop`, `tmux`, and Vim's package payload. The hook configures the
system `pager` alternative to use `less` and recreates Vim's missing Debian
alternatives so both `vi` and `vim` resolve to `vim.basic`. This is deliberate:
Docker's v3 recipe guidance notes that APT packages depend on the composed
base's dpkg database and shared-library closure, so copying them into a
generic mixin overlay would be less portable and could be broken. The hook
uses `--no-install-recommends` and removes the APT lists after installation.
Package versions follow the selected shell workload's repository and security
updates; they are not claimed as immutable application-release artifacts.

## Customize the workload

With these security and network boundaries in mind, customize the checked-in
source files, not the generated descriptors. The published
`sbx-kit-pifrost.yaml` is a workload descriptor with the generated
`sbx-kit-pifrost.dockerfile`; the descriptor is self-contained for its inline
lifecycle content. `sbx-kit-pifrost-dod-certs.yaml` remains a separate mixin.
The optional certificate mixin also has a generated companion Dockerfile,
which copies the certificate snapshot into its image layer; Docker Buildx
consumes that recipe and the `certificates/` context when it builds the mixin.

### Source files

- `files/.bashrc`, `files/.bash_aliases`, `files/.dircolors`, and
  `files/sandbox-persistent.sh` define the shell environment.
- `files/models.json`, `files/settings.json`, and
  `files/themes/solarized-dark.json` provide the checked-in Pi configuration.
- `certificates/` contains the DoD/host trust certificate snapshot used by the
  optional mixin. Refresh it deliberately when the approved host certificates
  change.
- `scripts/render-kit-set.py` defines both descriptors, the pinned shell and Pi
  payload references, lifecycle commands, credentials, and network policy.
- `sbx-kit-pifrost.yaml`, `sbx-kit-pifrost.dockerfile`,
  `sbx-kit-pifrost-dod-certs.yaml`, and
  `sbx-kit-pifrost-dod-certs.dockerfile` are generated output. Do not edit them
  by hand.

For reproducibility, rendering uses the checked-in snapshots in `files/` by
default. To intentionally publish the current host Pi configuration instead,
pass the explicit opt-in flag:

```console
$ python3 scripts/render-kit-set.py --use-host-pi-config
```

The matching host files are:

```text
~/.pi/agent/models.json
~/.pi/agent/settings.json
~/.pi/agent/themes/solarized-dark.json
```

Review any host-derived changes before publishing. For a fully reviewable
build, copy the intended host versions into `files/` and render without the
flag.

### Render and validate a customized workload

After changing any source file, regenerate the descriptor:

```console
$ python3 scripts/render-kit-set.py
$ git diff -- files certificates scripts/render-kit-set.py \
    sbx-kit-pifrost.yaml sbx-kit-pifrost.dockerfile \
    sbx-kit-pifrost-dod-certs.yaml sbx-kit-pifrost-dod-certs.dockerfile
```

Validate the renderer without leaving Python bytecode in this WSL/virtiofs
checkout:

```console
$ scripts/validate-python.sh
```

The wrapper compiles the renderer with `PYTHONPYCACHEPREFIX` set to a temporary
normal-filesystem location and removes the cache afterward.

Build local OCI artifacts to validate both descriptors:

```console
$ docker buildx build . -f ./sbx-kit-pifrost.yaml \
    -t sbx-kit-pifrost:[version] --provenance=false \
    --output type=oci,dest=/tmp/sbx-kit-pifrost.oci.tar
$ docker buildx build . -f ./sbx-kit-pifrost-dod-certs.yaml \
    -t sbx-kit-pifrost-dod-certs:1.0.0 --provenance=false \
    --output type=oci,dest=/tmp/sbx-kit-pifrost-dod-certs.oci.tar
```

Running the Linux `sbx` CLI from WSL with a native `/home/...` workspace avoids
the outside-client path translation that originally motivated this workaround;
it is not normally required as a preparation step. If a workspace is still
presented through a WSL `virtiofs` mount and BuildKit reports
`failed to xattr ...: input/output error`, copy the project to a normal local
filesystem before building:

```console
$ rm -rf /tmp/sbx-kit-pifrost-build
$ mkdir -p /tmp/sbx-kit-pifrost-build
$ tar --exclude=.git -cf - . | tar -xf - -C /tmp/sbx-kit-pifrost-build
$ cd /tmp/sbx-kit-pifrost-build
$ docker buildx build . -f ./sbx-kit-pifrost.yaml \
    -t sbx-kit-pifrost:[version] --provenance=false \
    --output type=oci,dest=/tmp/sbx-kit-pifrost.oci.tar
$ docker buildx build . -f ./sbx-kit-pifrost-dod-certs.yaml \
    -t sbx-kit-pifrost-dod-certs:1.0.0 --provenance=false \
    --output type=oci,dest=/tmp/sbx-kit-pifrost-dod-certs.oci.tar
```

### Publish a customized version

The preferred publisher is a sandbox created from this kit because the
included shell workload provides a sandbox-local Docker Engine and Buildx
builder. Authenticate the host first with `sbx login`, then from the sandbox
workspace render and publish your chosen tag:

```console
$ docker context show       # expected: default
$ docker info --format 'server={{.Name}} root={{.DockerRootDir}}'
$ docker buildx ls           # expected: default* with driver `docker`
$ docker buildx inspect --bootstrap

$ python3 scripts/render-kit-set.py
$ rm -rf /tmp/sbx-kit-pifrost-build
$ mkdir -p /tmp/sbx-kit-pifrost-build
$ tar --exclude=.git -cf - . | tar -xf - -C /tmp/sbx-kit-pifrost-build
$ cd /tmp/sbx-kit-pifrost-build
$ docker buildx build . -f ./sbx-kit-pifrost.yaml \
    -t docker.io/choziandi/sbx-kit-pifrost:[tag] --push
$ docker buildx build . -f ./sbx-kit-pifrost-dod-certs.yaml \
    -t docker.io/choziandi/sbx-kit-pifrost-dod-certs:1.0.0 --push
```

Publish the certificate mixin only if you intend to offer the approved DoD
roots to users. Verify each published artifact:

```console
$ docker buildx imagetools inspect docker.io/choziandi/sbx-kit-pifrost:[tag]
$ docker buildx imagetools inspect \
    docker.io/choziandi/sbx-kit-pifrost-dod-certs:1.0.0
```

If you publish under another Docker Hub namespace, replace the image name and
use the same name in `sbx run`. A host-side Buildx fallback is also possible,
but it uses the Docker CLI credential store rather than the Sandboxes proxy:

```console
$ docker login
$ docker buildx build . -f ./sbx-kit-pifrost.yaml \
    -t docker.io/<namespace>/sbx-kit-pifrost:<version> --push
$ docker buildx build . -f ./sbx-kit-pifrost-dod-certs.yaml \
    -t docker.io/<namespace>/sbx-kit-pifrost-dod-certs:1.0.0 --push
```

When changing the workload version or the pinned shell/Pi references, update
the corresponding values in `scripts/render-kit-set.py`, rerender, validate,
and publish a new tag. The current published repository is
<https://hub.docker.com/r/choziandi/sbx-kit-pifrost>.

## Testing limitations

A Docker Sandbox used as the development environment cannot be assumed to
run local `sbx` end-to-end tests. It may not have the `sbx` CLI, and the
sandbox is itself a guest; when it lacks the `vmx` or `svm` CPU flags and
`/dev/kvm`, it cannot launch another local KVM-backed sandbox. These
limitations describe the nested development environment, not necessarily the
WSL Ubuntu host on which the project is intended to run.

Run end-to-end tests from the WSL Ubuntu host with KVM and nested
virtualization, or use Docker Cloud Sandboxes. Test at least:

- Bifrost credential registration and approval;
- `python --version`, `vim`, `tmux`, `htop`, and `git log` in a new sandbox;
- DoD-trusted TLS in a sandbox created with the certificate mixin, plus the Pi
  `models.json`, `settings.json`, and `themes/solarized-dark.json` files;
- `pi update` with the runtime npm allow; and
- the effective local and organization network policies.

## License

MIT
