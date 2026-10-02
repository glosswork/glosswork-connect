"""What the built Claude Desktop extension does against a real workspace.

These tests run the manifest's own argument list against the bundle they build, so what
they measure is the file a person installs rather than a copy of its intentions.

They need Docker, Node, the `cscheide/gw:rev1` image and macOS, so they never run in CI:
the `harness` marker excludes them by default and `pyproject.toml` records it. Run them
as the local gate:

    GLOSSWORK_HARNESS=1 uv run pytest -q -m harness

**The environment variable is what makes the gate honest.** Without it a missing
prerequisite skips, and `pytest -m harness` exits 0 on a machine that ran nothing. With
it a missing prerequisite is a failure, so exit 0 means these ran.

Every proxy invocation here, including the ones expected to try, runs with a shim named
`open` first on `PATH`. No browser is ever opened, and an empty shim log is the evidence
that none would have been.
"""

import datetime
import json
import os
import platform
import shutil
import socket
import subprocess
import threading
import time
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

pytestmark = pytest.mark.harness

REPO_ROOT = Path(__file__).resolve().parents[1]
SUPPORT = Path(__file__).parent / "support"
MCPB = REPO_ROOT / "mcpb"
BUNDLE_FILE = MCPB / "dist" / "glosswork.mcpb"

IMAGE = "docker.io/glosswork/glosswork:latest"
CONTAINER = "conn05-gw"
VOLUME = "conn05-data"
MCPB_VERSION = "2.1.2"

# A property of the token's scope, not of the product's tool list: an `admin` token sees
# 32 and a `read` token sees 11, and `describe_capabilities` is in both, so the count is
# the only thing that says which token is in use.
ADMIN_TOOL_COUNT = 32
READ_TOOL_COUNT = 11

# The proxy's own localhost test is an exact string match on `localhost` and `127.0.0.1`,
# so this fully qualified spelling of the same name is "not local" to it while still
# resolving to loopback. It exercises --allow-http without putting a workspace on a real
# network.
NON_LOCAL_HOST = "localhost."

PROXY_TIMEOUT_SECONDS = 60


def unmet(reason: str) -> None:
    """A missing prerequisite is a skip on a laptop and a failure on the gate."""
    if os.environ.get("GLOSSWORK_HARNESS") == "1":
        pytest.fail(f"harness prerequisite missing, and GLOSSWORK_HARNESS=1: {reason}")
    pytest.skip(f"harness prerequisite missing: {reason}")


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, **kwargs)  # type: ignore[arg-type]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def npm_environment(cache: Path) -> dict[str, str]:
    """npm's default cache is not usable on every machine, and `npx` reaches for the
    same one `npm ci` does, so every npm command here gets a cache it owns."""
    environment = os.environ.copy()
    cache.mkdir(parents=True, exist_ok=True)
    environment["npm_config_cache"] = str(cache)
    return environment


@pytest.fixture(scope="session")
def harness_ready() -> None:
    if platform.system() != "Darwin":
        unmet("these tests were measured on macOS only, and the `open` shim only detects there")
    for tool in ("docker", "node", "npx", "openssl"):
        if shutil.which(tool) is None:
            unmet(f"{tool} is not on PATH")
    if run(["docker", "info"]).returncode != 0:
        unmet("the Docker daemon is not answering")
    if run(["docker", "image", "inspect", IMAGE]).returncode != 0:
        unmet(f"the image {IMAGE} is not present")


@pytest.fixture(scope="session")
def bundle(harness_ready: None, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The built `.mcpb`, unpacked. Built first if it is not there already."""
    if not BUNDLE_FILE.exists():
        built = run(["bash", str(MCPB / "build.sh")])
        assert built.returncode == 0, built.stderr
    scratch = tmp_path_factory.mktemp("conn05-bundle")
    unpacked = scratch / "unpacked"
    unpacked.mkdir()
    result = run(
        ["npx", "--yes", f"@anthropic-ai/mcpb@{MCPB_VERSION}", "unpack", str(BUNDLE_FILE), "."],
        cwd=unpacked,
        env=npm_environment(scratch / "npm-cache"),
    )
    assert result.returncode == 0, result.stderr
    assert (unpacked / "manifest.json").is_file(), "the bundle carries no manifest"
    return unpacked


@dataclass
class Workspace:
    port: int
    admin_token: str
    read_token: str
    scratch: Path

    @property
    def address(self) -> str:
        """Spelled the way this workspace's own GW_BASE_URL spells it."""
        return f"http://127.0.0.1:{self.port}/mcp"

    @property
    def misspelled_address(self) -> str:
        """The same workspace, by a host its allowlist does not name."""
        return f"http://localhost:{self.port}/mcp"

    @property
    def non_local_address(self) -> str:
        return f"http://{NON_LOCAL_HOST}:{self.port}/mcp"

    def mint(self, name: str, scope: str, expires_at: str | None = None) -> str:
        command = [
            "docker", "exec", CONTAINER,
            "python", "-m", "glosswork.admin", "mint-token",
            "--name", name, "--scope", scope, "--quiet",
        ]  # fmt: skip
        if expires_at:
            command += ["--expires-at", expires_at]
        minted = run(command)
        assert minted.returncode == 0, minted.stderr
        return minted.stdout.strip()


@pytest.fixture(scope="session")
def workspace(harness_ready: None, tmp_path_factory: pytest.TempPathFactory) -> Iterator[Workspace]:
    """A scratch workspace, started and removed by this session.

    It is never a pilot's workspace: a pilot container holds real data, and this mints
    tokens in whatever it points at. `GW_BASE_URL` is set so the product's `Host`
    allowlist turns itself on, which is what makes the mismatch testable at all, and
    `GW_MCP_ALLOWED_HOSTS` adds the one non-local spelling the --allow-http test needs.
    """
    scratch = tmp_path_factory.mktemp("conn05-workspace")
    port = free_port()

    # The bootstrap password is generated, written to a file only this user can read, and
    # given to the container as an env file. It never appears on a command line.
    password = run(["openssl", "rand", "-base64", "24"]).stdout.strip()
    env_file = scratch / "gw.env"
    env_file.write_text(
        "\n".join(
            [
                f"GW_BASE_URL=http://127.0.0.1:{port}",
                f"GW_MCP_ALLOWED_HOSTS={NON_LOCAL_HOST}:{port}",
                "GW_BOOTSTRAP_ADMIN_EMAIL=conn05@example.invalid",
                f"GW_BOOTSTRAP_ADMIN_PASSWORD={password}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    env_file.chmod(0o600)

    run(["docker", "rm", "-f", CONTAINER])
    run(["docker", "volume", "rm", "-f", VOLUME])
    assert run(["docker", "volume", "create", VOLUME]).returncode == 0
    started = run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            CONTAINER,
            "--env-file",
            str(env_file),
            "-v",
            f"{VOLUME}:/data",
            "-p",
            f"127.0.0.1:{port}:8000",
            IMAGE,
        ]  # fmt: skip
    )
    assert started.returncode == 0, started.stderr

    ready = False
    for _ in range(90):
        probe = run(
            [
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                f"http://127.0.0.1:{port}/readyz",
            ]
        )
        if probe.stdout.strip() == "200":
            ready = True
            break
        time.sleep(1)
    assert ready, "the scratch workspace never answered /readyz with 200"

    prepared = Workspace(
        port=port,
        admin_token="",
        read_token="",
        scratch=scratch,
    )
    prepared.admin_token = prepared.mint("conn05-desktop", "admin")
    prepared.read_token = prepared.mint("conn05-read", "read")

    yield prepared

    run(["docker", "rm", "-f", CONTAINER])
    run(["docker", "volume", "rm", "-f", VOLUME])


@dataclass
class ProxyRun:
    returncode: int
    stderr: str
    tools: list[str] = field(default_factory=list)
    shim_lines: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)


def manifest_command(bundle: Path, address: str) -> tuple[list[str], str]:
    """The manifest's own command and argument list, with the two substitutions Claude
    Desktop would make. Reading it from the bundle is the point: a test that spelled the
    arguments out again would pass while the shipped manifest said something else."""
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    config = manifest["server"]["mcp_config"]
    arguments = [
        argument.replace("${__dirname}", str(bundle)).replace("${user_config.address}", address)
        for argument in config["args"]
    ]
    (token_variable,) = config["env"]
    return [config["command"], *arguments], token_variable


def proxy_run(
    bundle: Path,
    address: str,
    token: str | None,
    scratch: Path,
    drop_arguments: tuple[str, ...] = (),
    extra_environment: dict[str, str] | None = None,
    timeout: float = PROXY_TIMEOUT_SECONDS,
) -> ProxyRun:
    """Run the bundled proxy over stdio, ask for the tool list, and report what happened.

    `token=None` means the environment variable is absent entirely, which is a distinct
    case: the proxy then sends the literal `${GLOSSWORK_TOKEN}` as the bearer value.
    """
    command, token_variable = manifest_command(bundle, address)
    command = [part for part in command if part not in drop_arguments]

    run_directory = Path(scratch)
    run_directory.mkdir(parents=True, exist_ok=True)
    shim_directory = run_directory / "shim"
    shim_directory.mkdir(exist_ok=True)
    shim_log = run_directory / "open.log"
    shim = shim_directory / "open"
    shim.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$*" >> "$OPEN_SHIM_LOG"\nexit 0\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    config_directory = run_directory / "mcp-remote-config"
    config_directory.mkdir(exist_ok=True)

    environment = os.environ.copy()
    environment["PATH"] = f"{shim_directory}{os.pathsep}{environment['PATH']}"
    environment["OPEN_SHIM_LOG"] = str(shim_log)
    environment["MCP_REMOTE_CONFIG_DIR"] = str(config_directory)
    environment.pop(token_variable, None)
    if token is not None:
        environment[token_variable] = token
    if extra_environment:
        environment.update(extra_environment)

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    assert process.stdin and process.stdout and process.stderr

    collected: list[str] = []
    reader = threading.Thread(target=lambda: collected.append(process.stderr.read()))
    reader.daemon = True
    reader.start()

    def send(message: dict[str, object]) -> None:
        assert process.stdin
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    # A proxy that reaches the OAuth path waits for a callback that will never come, and
    # `readline` blocks, so a deadline checked between lines never fires. The watchdog
    # kills the process, which closes stdout and ends the loop.
    watchdog = threading.Timer(timeout, process.kill)
    watchdog.daemon = True
    watchdog.start()

    tools: list[str] = []
    try:
        send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "conn05-harness", "version": "0"},
                },
            }
        )
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        while True:
            line = process.stdout.readline()
            if not line:
                break
            try:
                message = json.loads(line)
            except ValueError:
                continue
            if message.get("id") == 2:
                tools = sorted(tool["name"] for tool in message.get("result", {}).get("tools", []))
                break
    except (BrokenPipeError, OSError):
        pass
    finally:
        watchdog.cancel()

    try:
        process.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    try:
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=10)
    reader.join(timeout=5)

    return ProxyRun(
        returncode=process.returncode,
        stderr="".join(chunk for chunk in collected if chunk),
        tools=tools,
        shim_lines=[
            line for line in shim_log.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        if shim_log.exists()
        else [],
        config_files=[str(path) for path in config_directory.rglob("*") if path.is_file()],
    )


@dataclass
class Listener:
    process: subprocess.Popen[str]
    port: int

    def stop(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()


def start_node(script: Path, arguments: list[str], port: int) -> Listener:
    process = subprocess.Popen(
        ["node", str(script), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return Listener(process=process, port=port)
        time.sleep(0.2)
    process.kill()
    raise AssertionError(f"{script.name} never listened on {port}")


# --------------------------------------------------------------------------------------
# Tools list
# --------------------------------------------------------------------------------------


def test_tools_over_http_on_loopback(bundle: Path, workspace: Workspace, tmp_path: Path) -> None:
    """The whole point of the extension, over the address the workspace itself names."""
    result = proxy_run(bundle, workspace.address, workspace.admin_token, tmp_path)
    assert result.returncode == 0, result.stderr
    assert len(result.tools) == ADMIN_TOOL_COUNT, result.tools
    assert "describe_capabilities" in result.tools
    assert result.shim_lines == []


def test_tools_over_http_reflect_the_tokens_scope(
    bundle: Path, workspace: Workspace, tmp_path: Path
) -> None:
    """`describe_capabilities` is in both lists, so the count is the only thing that says
    which token is in use. An install check that records only the name sees nothing."""
    result = proxy_run(bundle, workspace.address, workspace.read_token, tmp_path)
    assert result.returncode == 0, result.stderr
    assert len(result.tools) == READ_TOOL_COUNT, result.tools
    assert "describe_capabilities" in result.tools


def test_tools_over_https_through_a_relay(
    bundle: Path, workspace: Workspace, tmp_path: Path
) -> None:
    """The proxy speaks TLS. This does NOT prove a self-hosted HTTPS workspace is
    reachable: it works because NODE_EXTRA_CA_CERTS points Node at the scratch
    certificate, and nothing in the shipped manifest can set that variable."""
    certificate = tmp_path / "relay.pem"
    key = tmp_path / "relay.key"
    generated = run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(certificate),
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost",
        ]  # fmt: skip
    )
    assert generated.returncode == 0, generated.stderr

    port = free_port()
    relay = start_node(
        SUPPORT / "relay.mjs",
        [
            "--listen",
            str(port),
            "--upstream",
            f"127.0.0.1:{workspace.port}",
            "--log",
            str(tmp_path / "headers.jsonl"),
            "--tls-cert",
            str(certificate),
            "--tls-key",
            str(key),
        ],  # fmt: skip
        port,
    )
    try:
        result = proxy_run(
            bundle,
            f"https://localhost:{port}/mcp",
            workspace.admin_token,
            tmp_path,
            extra_environment={"NODE_EXTRA_CA_CERTS": str(certificate)},
        )
    finally:
        relay.stop()
    assert result.returncode == 0, result.stderr
    assert len(result.tools) == ADMIN_TOOL_COUNT, result.tools
    assert result.shim_lines == []


def test_agent_label_is_on_every_request_that_carries_the_token(
    bundle: Path, workspace: Workspace, tmp_path: Path
) -> None:
    """The label is what a person reads in the workspace's history to see which tool made
    a change, and the workspace records it on a write. Every request that carries the
    token carries the label with it.

    **Not every request the proxy makes carries either.** Measured here: `mcp-remote`
    sends unauthenticated `GET` requests to `.well-known` discovery paths of its own,
    with browser-shaped headers and none of the `--header` values. They authenticate
    nothing, write nothing and are refused, so the label's promise is about the requests
    that act, and this test states it that way rather than over-claiming.
    """
    log = tmp_path / "headers.jsonl"
    port = free_port()
    relay = start_node(
        SUPPORT / "relay.mjs",
        [
            "--listen",
            str(port),
            "--upstream",
            f"127.0.0.1:{workspace.port}",
            "--log",
            str(log),
        ],  # fmt: skip
        port,
    )
    try:
        result = proxy_run(bundle, f"http://127.0.0.1:{port}/mcp", workspace.admin_token, tmp_path)
    finally:
        relay.stop()
    assert result.returncode == 0, result.stderr

    entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]
    assert entries, "the relay recorded no request at all"

    authorized = [entry for entry in entries if entry["hasAuthorization"]]
    assert authorized, "no request carried the token, so the label proves nothing"
    for entry in authorized:
        assert entry["agentLabel"] == "claude-desktop", entry
        assert entry["path"].endswith("/mcp"), entry

    # Nothing anywhere carries a label that is not ours, and the log holds no header
    # value other than the label itself.
    for entry in entries:
        assert entry["agentLabel"] in (None, "claude-desktop"), entry
        assert set(entry) == {"method", "path", "names", "hasAuthorization", "agentLabel"}, entry
        assert all(isinstance(name, str) for name in entry["names"])

    unauthenticated = [entry for entry in entries if not entry["hasAuthorization"]]
    for entry in unauthenticated:
        assert ".well-known" in entry["path"], entry
        assert entry["method"] == "GET", entry


# --------------------------------------------------------------------------------------
# The address, which is the thing most likely to be wrong
# --------------------------------------------------------------------------------------


def test_host_mismatch_is_a_421_that_names_nothing(
    bundle: Path, workspace: Workspace, tmp_path: Path
) -> None:
    """The same workspace and the same token, addressed by the other spelling of its own
    host. The product matches `Host` against an exact `host:port`, so this fails, and the
    message names neither the address nor the fix. It is why the README carries it."""
    result = proxy_run(bundle, workspace.misspelled_address, workspace.admin_token, tmp_path)
    assert result.returncode != 0
    assert "Invalid Host header" in result.stderr
    assert "421" in result.stderr
    assert result.tools == []


def test_allow_http_reaches_an_address_that_is_not_on_this_machine(
    bundle: Path, workspace: Workspace, tmp_path: Path
) -> None:
    """Q51. The flag the manifest ships is what lets a person reach a workspace on their
    own network over plain HTTP."""
    result = proxy_run(bundle, workspace.non_local_address, workspace.admin_token, tmp_path)
    assert result.returncode == 0, result.stderr
    assert len(result.tools) == ADMIN_TOOL_COUNT, result.tools


def test_allow_http_is_the_only_thing_that_makes_that_work(
    bundle: Path, workspace: Workspace, tmp_path: Path
) -> None:
    """The same address with the flag removed. Without it the proxy refuses before it
    sends anything, which is what the extension did before Q51."""
    result = proxy_run(
        bundle,
        workspace.non_local_address,
        workspace.admin_token,
        tmp_path,
        drop_arguments=("--allow-http",),
    )
    assert result.returncode != 0
    assert "Non-HTTPS URLs are only allowed for localhost" in result.stderr


# --------------------------------------------------------------------------------------
# The token, and the browser that must not open
# --------------------------------------------------------------------------------------


def assert_failed_without_a_browser(result: ProxyRun) -> None:
    assert result.returncode != 0
    assert result.shim_lines == [], result.shim_lines
    assert result.config_files == [], result.config_files


def test_token_wrong_value(bundle: Path, workspace: Workspace, tmp_path: Path) -> None:
    result = proxy_run(bundle, workspace.address, "gw" + "_pat_" + "notarealtoken", tmp_path)
    assert_failed_without_a_browser(result)
    assert "cannot verify" in result.stderr


def test_token_wrong_because_it_is_empty(
    bundle: Path, workspace: Workspace, tmp_path: Path
) -> None:
    result = proxy_run(bundle, workspace.address, "", tmp_path)
    assert_failed_without_a_browser(result)


def test_token_wrong_because_the_variable_is_absent(
    bundle: Path, workspace: Workspace, tmp_path: Path
) -> None:
    """With nothing in the environment the proxy sends the literal `${GLOSSWORK_TOKEN}`
    as the bearer value, which the workspace refuses like any other bad token."""
    result = proxy_run(bundle, workspace.address, None, tmp_path)
    assert_failed_without_a_browser(result)


def test_token_wrong_because_it_expired(bundle: Path, workspace: Workspace, tmp_path: Path) -> None:
    """An expired token reads differently from a wrong one: the workspace names the
    expiry and says to mint a replacement. A past expiry cannot be minted, so this mints
    one a few seconds ahead and waits for it."""
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=5)
    token = workspace.mint("conn05-expired", "read", expires_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
    time.sleep(8)
    result = proxy_run(bundle, workspace.address, token, tmp_path)
    assert_failed_without_a_browser(result)
    assert "expired" in result.stderr.lower()


def test_a_successful_run_writes_nothing_to_the_proxys_config_directory(
    bundle: Path, workspace: Workspace, tmp_path: Path
) -> None:
    """Nothing derived from the token reaches disk, on success either."""
    result = proxy_run(bundle, workspace.address, workspace.admin_token, tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.config_files == [], result.config_files


@pytest.mark.parametrize(
    ("mode", "opens"),
    [
        ("metadata", True),
        ("json404", False),
        ("html200", False),
        ("redirect", False),
    ],
)
def test_browser_detector_fires_only_against_a_real_authorization_server(
    bundle: Path, tmp_path: Path, mode: str, opens: bool
) -> None:
    """Three things must all hold before `mcp-remote` opens a browser: a 401, parseable
    OAuth metadata, and a dynamic client registration that succeeds. `metadata` is the
    only stub with all three, and it must open one, or an empty shim log in the other
    three would prove nothing. `html200` is what the product answers today.
    """
    port = free_port()
    stub = start_node(
        SUPPORT / "stub_oauth.mjs",
        ["--mode", mode, "--listen", str(port)],
        port,
    )
    try:
        # The metadata stub's proxy reaches openBrowser and then waits for a callback
        # that will never arrive, so this one ends on the watchdog rather than on its own.
        result = proxy_run(
            bundle, f"http://127.0.0.1:{port}/mcp", "conn05-irrelevant", tmp_path, timeout=25
        )
    finally:
        stub.stop()

    if opens:
        assert len(result.shim_lines) == 1, result.shim_lines
        assert "/authorize" in result.shim_lines[0]
    else:
        assert result.shim_lines == [], result.shim_lines
        assert result.returncode != 0


# --------------------------------------------------------------------------------------
# What the bundle file carries
# --------------------------------------------------------------------------------------


def bundle_entries() -> list[str]:
    with zipfile.ZipFile(BUNDLE_FILE) as archive:
        return archive.namelist()


def test_the_bundle_root_holds_only_the_manifest_and_package_json(bundle: Path) -> None:
    """Read from the zip listing of the file a person installs. The build script and the
    README stay out, and the proxy's own README stays in, which is what an ignore pattern
    that is not anchored to the root would strip."""
    entries = bundle_entries()
    root_entries = sorted(name for name in entries if "/" not in name)
    assert root_entries == ["manifest.json", "package.json"], root_entries
    assert "node_modules/mcp-remote/README.md" in entries


def test_the_bundled_manifest_is_the_source_manifest(bundle: Path) -> None:
    """The structural tests read `mcpb/manifest.json`. They say something about the shipped
    extension only while the manifest inside the bundle is that file, byte for byte."""
    with zipfile.ZipFile(BUNDLE_FILE) as archive:
        shipped = archive.read("manifest.json")
    assert shipped == (MCPB / "manifest.json").read_bytes()
