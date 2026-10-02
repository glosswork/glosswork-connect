// Four servers that a Glosswork workspace could be mistaken for, behind one --mode
// flag. They exist to answer one question: when does mcp-remote open a browser?
//
//   metadata : 401, parseable OAuth metadata, and dynamic client registration that
//              succeeds. This is the only shape that reaches openBrowser, and the
//              harness asserts that it DOES, so that the detector is known to work.
//   json404  : 401, and 404 JSON on every .well-known path. This is what the product
//              would answer after the proposed fix to its .well-known handling.
//   html200  : 401, and 200 with the browser app's HTML on every .well-known path.
//              This is what the product answers today.
//   redirect : 302 to a sign-in page for everything, which is what an access proxy or
//              a tunnel puts in front of a workspace.
//
// One file rather than four, because they differ by a few lines and the point is the
// contrast between them.
//
// Usage: node stub_oauth.mjs --mode <name> --listen <port>

import http from 'node:http'

function option(name, fallback = null) {
  const index = process.argv.indexOf(`--${name}`)
  return index === -1 ? fallback : process.argv[index + 1]
}

const mode = option('mode')
const listenPort = Number(option('listen'))
const origin = `http://127.0.0.1:${listenPort}`

const HTML = '<!doctype html><html><body><div id="root"></div></body></html>'

function json(response, status, body, headers = {}) {
  response.writeHead(status, { 'content-type': 'application/json', ...headers })
  response.end(JSON.stringify(body))
}

const server = http.createServer((request, response) => {
  const path = new URL(request.url, origin).pathname

  if (mode === 'redirect') {
    response.writeHead(302, { location: `${origin}/sign-in` })
    response.end()
    return
  }

  if (path.startsWith('/.well-known') || path.includes('/.well-known')) {
    if (mode === 'metadata') {
      if (path.includes('oauth-protected-resource')) {
        json(response, 200, { resource: `${origin}/mcp`, authorization_servers: [origin] })
        return
      }
      json(response, 200, {
        issuer: origin,
        authorization_endpoint: `${origin}/authorize`,
        token_endpoint: `${origin}/token`,
        registration_endpoint: `${origin}/register`,
        response_types_supported: ['code'],
        grant_types_supported: ['authorization_code', 'refresh_token'],
        code_challenge_methods_supported: ['S256'],
        token_endpoint_auth_methods_supported: ['none', 'client_secret_post'],
        scopes_supported: ['openid'],
      })
      return
    }
    if (mode === 'json404') {
      json(response, 404, { error: 'not_found' })
      return
    }
    // html200: the shape the product serves today, a single page app on every path.
    response.writeHead(200, { 'content-type': 'text/html' })
    response.end(HTML)
    return
  }

  if (mode === 'metadata' && path === '/register') {
    json(response, 201, {
      client_id: 'kit-harness-stub-client',
      redirect_uris: [`${origin}/callback`],
      token_endpoint_auth_method: 'none',
      grant_types: ['authorization_code', 'refresh_token'],
      response_types: ['code'],
    })
    return
  }

  // Everything else, including /mcp, is unauthorized. The metadata mode points at its
  // own resource metadata, which is the first step of the path that ends in a browser.
  const headers =
    mode === 'metadata'
      ? {
          'www-authenticate': `Bearer resource_metadata="${origin}/.well-known/oauth-protected-resource"`,
        }
      : {}
  json(response, 401, { error: 'unauthorized' }, headers)
})

server.listen(listenPort, '127.0.0.1', () => {
  process.stdout.write(`stub ${mode} listening on ${listenPort}\n`)
})
