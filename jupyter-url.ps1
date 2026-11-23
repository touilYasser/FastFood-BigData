$ErrorActionPreference = 'Stop'

Push-Location -LiteralPath $PSScriptRoot
try {
    $binding = docker compose port jupyter 8888
    if ($LASTEXITCODE -ne 0 -or $binding -notmatch '^127\.0\.0\.1:(\d+)$') {
        throw 'Jupyter est inaccessible. Lance docker compose up -d --wait puis consulte docker compose ps -a.'
    }
    $port = $Matches[1]

    $servers = docker compose exec -T jupyter jupyter server list --json
    if ($LASTEXITCODE -ne 0 -or -not $servers) {
        throw 'Le serveur Jupyter ne repond pas encore. Consulte docker compose logs --tail 50 jupyter.'
    }

    $server = $servers | ConvertFrom-Json | Where-Object port -eq 8888 | Select-Object -First 1
    if (-not $server) {
        throw 'Le serveur Jupyter ne repond pas encore. Consulte docker compose logs --tail 50 jupyter.'
    }

    $url = "http://127.0.0.1:$port/"
    if ($server.token) {
        $url += '?token=' + [Uri]::EscapeDataString($server.token)
    }
    Write-Output $url
}
finally {
    Pop-Location
}
