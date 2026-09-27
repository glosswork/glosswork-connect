// A scratch reverse proxy for the harness tests. Two modes, one process:
//
//   plain HTTP  : forward to the upstream and record request headers
//   HTTPS       : terminate TLS with a certificate given to it, then the same
//
// Usage:
//   node relay.mjs --listen <port> --upstream <host:port> --log <path>
//                  [--tls-cert <path> --tls-key <path>]
//
// It rewrites the `Host` header to the upstream's own `host:port`. That is deliberate
// and load bearing: the product matches `Host` against an exact `host:port` allowlist
// as soon as GW_BASE_URL is set, so a relay that passed its own `Host` through would
// get 421 and the test would be measuring the relay rather than the bundle.
//
// It logs the method, the path, the header NAMES, whether an Authorization header was
// present, and the value of X-Agent-Label. It never logs any other header value and never
// logs a body, because one of the headers is the access token.

import { appendFileSync } from 'node:fs'
import { readFileSync } from 'node:fs'
import http from 'node:http'
import https from 'node:https'

function option(name, fallback = null) {
  const index = process.argv.indexOf(`--${name}`)
  return index === -1 ? fallback : process.argv[index + 1]
}

const listenPort = Number(option('listen'))
const upstream = option('upstream')
const logPath = option('log')
const tlsCert = option('tls-cert')
const tlsKey = option('tls-key')

const [upstreamHost, upstreamPort] = upstream.split(':')

const LABEL_HEADER = 'x-agent-label'

function record(request) {
  if (!logPath) return
  const headers = request.headers
  const entry = {
    method: request.method,
    path: request.url,
    names: Object.keys(headers).sort(),
    hasAuthorization: 'authorization' in headers,
    agentLabel: headers[LABEL_HEADER] ?? null,
  }
  appendFileSync(logPath, `${JSON.stringify(entry)}\n`)
}

function handle(request, response) {
  record(request)

  const forwarded = { ...request.headers, host: `${upstreamHost}:${upstreamPort}` }
  const proxied = http.request(
    {
      host: upstreamHost,
      port: upstreamPort,
      method: request.method,
      path: request.url,
      headers: forwarded,
    },
    (upstreamResponse) => {
      response.writeHead(upstreamResponse.statusCode, upstreamResponse.headers)
      upstreamResponse.pipe(response)
    },
  )
  proxied.on('error', (error) => {
    response.writeHead(502, { 'content-type': 'text/plain' })
    response.end(`relay: ${error.code ?? 'error'}`)
  })
  request.pipe(proxied)
}

const server =
  tlsCert && tlsKey
    ? https.createServer({ cert: readFileSync(tlsCert), key: readFileSync(tlsKey) }, handle)
    : http.createServer(handle)

server.listen(listenPort, '127.0.0.1', () => {
  process.stdout.write(`relay listening on ${listenPort}\n`)
})
