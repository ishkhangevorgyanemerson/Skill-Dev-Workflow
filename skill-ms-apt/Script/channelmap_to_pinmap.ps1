param(
    [Parameter(Mandatory = $true)]
    [string]$InputCsv,

    [Parameter(Mandatory = $true)]
    [string]$OutputPinmap
)

$ErrorActionPreference = 'Stop'

function Get-DeviceConfig {
    param([string]$DeviceNumber)

    switch ($DeviceNumber) {
        '6571' { return @{ DeviceType = 'HSD'; Element = 'NIDigitalPatternInstrument'; NumberOfChannels = '32' } }
        '4309' { return @{ DeviceType = 'DAC'; Element = 'NIDAQmxTask'; TaskType = 'AnalogInputVoltage'; ChannelListSuffix = 'ai0:31' } }
        '4463' { return @{ DeviceType = 'DSA'; Element = 'NIDAQmxTask'; TaskType = 'AnalogOutputVoltage'; ChannelListSuffix = 'ao0:1' } }
        '4163' { return @{ DeviceType = 'SMU'; Element = 'NIDCPowerInstrument'; NumberOfChannels = '24' } }
        '2567' { return @{ DeviceType = 'RELAY'; Element = 'NIRelayDriverModule'; NumberOfControlLines = '64' } }
        default { throw "Unsupported device number: $DeviceNumber" }
    }
}

function Parse-DeviceCell {
    param([string]$CellValue)

    if ([string]::IsNullOrWhiteSpace($CellValue) -or $CellValue -eq 'GND') {
        return $null
    }

    $match = [regex]::Match($CellValue.Trim(), '^(?<device>\d+)_(?<section>S\d+)_.+$')
    if (-not $match.Success) {
        throw "Unable to parse channel-map cell: $CellValue"
    }

    $deviceNumber = $match.Groups['device'].Value
    $section = $match.Groups['section'].Value
    $config = Get-DeviceConfig -DeviceNumber $deviceNumber
    $instrumentName = '{0}_{1}_C1_{2}' -f $config.DeviceType, $deviceNumber, $section

    return @{
        DeviceNumber = $deviceNumber
        Section = $section
        InstrumentName = $instrumentName
        Config = $config
    }
}

function Sanitize-PinName {
    param(
        [string]$NetName,
        [string]$DeviceType
    )

    $name = [regex]::Replace($NetName.Trim(), '[^A-Za-z0-9]', '_')
    $name = $name.TrimEnd('_')

    if (-not [string]::IsNullOrWhiteSpace($name) -and [char]::IsDigit($name[0])) {
        $name = '{0}_{1}' -f $DeviceType, $name
    }

    return $name
}

function Get-ConnectionChannel {
    param(
        [string]$CellValue,
        [string]$DeviceNumber,
        [string]$InstrumentName
    )

    $trimmed = $CellValue.Trim()
    $channelMatch = [regex]::Match($trimmed, 'CH(?<ch>\d+)')
    if ($channelMatch.Success) {
        $channel = $channelMatch.Groups['ch'].Value
    }
    else {
        $channel = ($trimmed -split '_')[-1].TrimEnd('+', '-', ' ')
    }

    switch ($DeviceNumber) {
        '4309' { return '{0}/ai{1}' -f $InstrumentName, $channel }
        '4463' { return '{0}/ao{1}' -f $InstrumentName, $channel }
        default { return $channel }
    }
}

function Get-NormalizedGroupPrefix {
    param([string]$PinName)

    $tokens = $PinName -split '_'
    $normalizedTokens = New-Object System.Collections.Generic.List[string]

    for ($i = 0; $i -lt $tokens.Count; $i++) {
        $token = $tokens[$i]
        if ([string]::IsNullOrWhiteSpace($token)) {
            continue
        }

        if ($token -match '^\d+$') {
            $normalized = $token
        }
        else {
            $normalized = [regex]::Replace($token, '\d+$', '')
            if ([string]::IsNullOrWhiteSpace($normalized)) {
                $normalized = $token
            }
        }

        if ($normalizedTokens.Count -eq 0 -or $normalizedTokens[$normalizedTokens.Count - 1] -ne $normalized) {
            $normalizedTokens.Add($normalized)
        }
    }

    return ($normalizedTokens -join '_')
}

function Get-RelayControlLine {
    param([string]$CellValue)

    $match = [regex]::Match($CellValue.Trim(), 'CH(?<ch>\d+)')
    if (-not $match.Success) {
        throw "Unable to extract relay control line from: $CellValue"
    }

    return 'K{0}' -f $match.Groups['ch'].Value
}

function ConvertFrom-CsvLines {
    param([string[]]$Lines)

    if (-not $Lines -or $Lines.Count -eq 0) {
        return @()
    }

    $csvText = ($Lines -join [Environment]::NewLine)
    return @($csvText | ConvertFrom-Csv)
}

if (-not (Test-Path -LiteralPath $InputCsv)) {
    throw "Input channel map file not found: $InputCsv"
}

$rawLines = Get-Content -LiteralPath $InputCsv
$relayHeaderIndex = -1
for ($i = 0; $i -lt $rawLines.Count; $i++) {
    if ($rawLines[$i] -match '^RELAY,NET NAME,') {
        $relayHeaderIndex = $i
        break
    }
}

if ($relayHeaderIndex -lt 1) {
    throw 'Relay table header was not found in the channel map CSV.'
}

$pinSectionLines = @($rawLines[0..($relayHeaderIndex - 1)] | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch '^,+$' })
$relaySectionLines = @($rawLines[$relayHeaderIndex..($rawLines.Count - 1)] | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch '^,+$' })

$pinRows = ConvertFrom-CsvLines -Lines $pinSectionLines
$relayRows = ConvertFrom-CsvLines -Lines $relaySectionLines

if (-not $pinRows -or $pinRows.Count -eq 0) {
    throw 'No pin-table rows were found in the channel map CSV.'
}

$siteColumns = @($pinRows[0].PSObject.Properties.Name | Where-Object { $_ -match '^SITE\d+$' } | Sort-Object)
if (-not $siteColumns -or $siteColumns.Count -eq 0) {
    throw 'No SITE columns were found in the pin table.'
}

$pinRowSeen = @{}
$relayRowSeen = @{}
$uniquePinRows = New-Object System.Collections.Generic.List[object]
$uniqueRelayRows = New-Object System.Collections.Generic.List[object]

foreach ($row in $pinRows) {
    $netName = [string]$row.'Net Name'
    if ([string]::IsNullOrWhiteSpace($netName) -or $netName.Trim().ToUpperInvariant() -eq 'GND') {
        continue
    }

    $rowKeyParts = New-Object System.Collections.Generic.List[string]
    $rowKeyParts.Add($netName.Trim())
    foreach ($site in $siteColumns) {
        $rowKeyParts.Add([string]$row.$site)
    }
    $rowKey = $rowKeyParts -join '|'
    if (-not $pinRowSeen.ContainsKey($rowKey)) {
        $pinRowSeen[$rowKey] = $true
        $uniquePinRows.Add($row)
    }
}

foreach ($row in $relayRows) {
    $relayName = [string]$row.RELAY
    $netName = [string]$row.'NET NAME'
    if ([string]::IsNullOrWhiteSpace($relayName) -or [string]::IsNullOrWhiteSpace($netName)) {
        continue
    }

    $rowKeyParts = New-Object System.Collections.Generic.List[string]
    $rowKeyParts.Add($relayName.Trim())
    $rowKeyParts.Add($netName.Trim())
    foreach ($site in $siteColumns) {
        $rowKeyParts.Add([string]$row.$site)
    }
    $rowKey = $rowKeyParts -join '|'
    if (-not $relayRowSeen.ContainsKey($rowKey)) {
        $relayRowSeen[$rowKey] = $true
        $uniqueRelayRows.Add($row)
    }
}

$instrumentOrder = New-Object System.Collections.Generic.List[string]
$instruments = @{}
$pins = New-Object System.Collections.Generic.List[string]
$pinSet = @{}
$pinGroups = @{}
$pinGroupOrder = New-Object System.Collections.Generic.List[string]
$connections = New-Object System.Collections.Generic.List[object]

foreach ($row in $uniquePinRows) {
    $netName = [string]$row.'Net Name'
    $firstParsed = $null
    foreach ($site in $siteColumns) {
        $cellValue = [string]$row.$site
        if (-not [string]::IsNullOrWhiteSpace($cellValue) -and $cellValue -ne 'GND') {
            $firstParsed = Parse-DeviceCell -CellValue $cellValue
            break
        }
    }

    if ($null -eq $firstParsed) {
        continue
    }

    $pinName = Sanitize-PinName -NetName $netName -DeviceType $firstParsed.Config.DeviceType
    if (-not $pinSet.ContainsKey($pinName)) {
        $pinSet[$pinName] = $true
        $pins.Add($pinName)

        $groupName = 'ALL_{0}' -f (Get-NormalizedGroupPrefix -PinName $pinName)
        if (-not $pinGroups.ContainsKey($groupName)) {
            $pinGroups[$groupName] = New-Object System.Collections.Generic.List[string]
            $pinGroupOrder.Add($groupName)
        }
        $pinGroups[$groupName].Add($pinName)
    }

    for ($siteIndex = 0; $siteIndex -lt $siteColumns.Count; $siteIndex++) {
        $site = $siteColumns[$siteIndex]
        $cellValue = [string]$row.$site
        if ([string]::IsNullOrWhiteSpace($cellValue) -or $cellValue -eq 'GND') {
            continue
        }

        $parsed = Parse-DeviceCell -CellValue $cellValue
        $instrumentKey = '{0}|{1}' -f $parsed.DeviceNumber, $parsed.Section
        if (-not $instruments.ContainsKey($instrumentKey)) {
            $instrumentOrder.Add($instrumentKey)
            $instruments[$instrumentKey] = $parsed
        }

        $connections.Add([pscustomobject]@{
            Kind = 'Pin'
            Pin = $pinName
            SiteNumber = [string]$siteIndex
            Instrument = $parsed.InstrumentName
            Channel = Get-ConnectionChannel -CellValue $cellValue -DeviceNumber $parsed.DeviceNumber -InstrumentName $parsed.InstrumentName
        })
    }
}

$relayGroupsByNet = @{}
$relayGroupOrder = New-Object System.Collections.Generic.List[string]
foreach ($row in $uniqueRelayRows) {
    $netName = [string]$row.'NET NAME'
    if (-not $relayGroupsByNet.ContainsKey($netName)) {
        $relayGroupsByNet[$netName] = New-Object System.Collections.Generic.List[object]
        $relayGroupOrder.Add($netName)
    }
    $relayGroupsByNet[$netName].Add($row)
}

$relayNames = New-Object System.Collections.Generic.List[string]
$relayConnections = New-Object System.Collections.Generic.List[object]

foreach ($netName in $relayGroupOrder) {
    $rowsForNet = $relayGroupsByNet[$netName]
    $relayNumbers = @($rowsForNet | ForEach-Object { [int](([string]$_.RELAY).TrimStart('K')) } | Sort-Object)
    if ($relayNumbers.Count -gt 1) {
        $relayName = 'K' + ($relayNumbers -join '_')
    }
    else {
        $relayName = 'K{0}' -f $relayNumbers[0]
    }
    $relayNames.Add($relayName)

    for ($siteIndex = 0; $siteIndex -lt $siteColumns.Count; $siteIndex++) {
        $site = $siteColumns[$siteIndex]
        $cellValue = [string]$rowsForNet[0].$site
        if ([string]::IsNullOrWhiteSpace($cellValue)) {
            continue
        }

        $parsed = Parse-DeviceCell -CellValue $cellValue
        $instrumentKey = '{0}|{1}' -f $parsed.DeviceNumber, $parsed.Section
        if (-not $instruments.ContainsKey($instrumentKey)) {
            $instrumentOrder.Add($instrumentKey)
            $instruments[$instrumentKey] = $parsed
        }

        $relayConnections.Add([pscustomobject]@{
            Relay = $relayName
            SiteNumber = [string]$siteIndex
            RelayDriverModule = $parsed.InstrumentName
            ControlLine = Get-RelayControlLine -CellValue $cellValue
        })
    }
}

$outputDir = Split-Path -Parent $OutputPinmap
if (-not (Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$settings = New-Object System.Xml.XmlWriterSettings
$settings.Indent = $true
$settings.IndentChars = "`t"
$settings.Encoding = New-Object System.Text.UTF8Encoding($false)

$writer = [System.Xml.XmlWriter]::Create($OutputPinmap, $settings)
$writer.WriteStartDocument()
$writer.WriteStartElement('PinMap', 'http://www.ni.com/TestStand/SemiconductorModule/PinMap.xsd')
$writer.WriteAttributeString('xmlns', 'xsi', $null, 'http://www.w3.org/2001/XMLSchema-instance')
$writer.WriteAttributeString('schemaVersion', '1.2')

$writer.WriteStartElement('Instruments')
foreach ($instrumentKey in $instrumentOrder) {
    $instrument = $instruments[$instrumentKey]
    $config = $instrument.Config
    $writer.WriteStartElement($config.Element)
    $writer.WriteAttributeString('name', $instrument.InstrumentName)
    switch ($config.Element) {
        'NIDigitalPatternInstrument' { $writer.WriteAttributeString('numberOfChannels', $config.NumberOfChannels) }
        'NIDCPowerInstrument' { $writer.WriteAttributeString('numberOfChannels', $config.NumberOfChannels) }
        'NIRelayDriverModule' { $writer.WriteAttributeString('numberOfControlLines', $config.NumberOfControlLines) }
        'NIDAQmxTask' {
            $writer.WriteAttributeString('taskType', $config.TaskType)
            $writer.WriteAttributeString('channelList', ('{0}/{1}' -f $instrument.InstrumentName, $config.ChannelListSuffix))
        }
    }
    $writer.WriteEndElement()
}
$writer.WriteEndElement()

$writer.WriteStartElement('Pins')
foreach ($pinName in $pins) {
    $writer.WriteStartElement('DUTPin')
    $writer.WriteAttributeString('name', $pinName)
    $writer.WriteEndElement()
}
$writer.WriteEndElement()

$writer.WriteStartElement('PinGroups')
foreach ($groupName in $pinGroupOrder) {
    $writer.WriteStartElement('PinGroup')
    $writer.WriteAttributeString('name', $groupName)
    foreach ($pinName in $pinGroups[$groupName]) {
        $writer.WriteStartElement('PinReference')
        $writer.WriteAttributeString('pin', $pinName)
        $writer.WriteEndElement()
    }
    $writer.WriteEndElement()
}
$writer.WriteEndElement()

$writer.WriteStartElement('Relays')
foreach ($relayName in $relayNames) {
    $writer.WriteStartElement('SiteRelay')
    $writer.WriteAttributeString('name', $relayName)
    $writer.WriteEndElement()
}
$writer.WriteEndElement()

$writer.WriteStartElement('RelayGroups')
$writer.WriteStartElement('RelayGroup')
$writer.WriteAttributeString('name', 'All_Relays')
foreach ($relayName in $relayNames) {
    $writer.WriteStartElement('RelayReference')
    $writer.WriteAttributeString('relay', $relayName)
    $writer.WriteEndElement()
}
$writer.WriteEndElement()
$writer.WriteEndElement()

$writer.WriteStartElement('Sites')
for ($siteIndex = 0; $siteIndex -lt $siteColumns.Count; $siteIndex++) {
    $writer.WriteStartElement('Site')
    $writer.WriteAttributeString('siteNumber', [string]$siteIndex)
    $writer.WriteEndElement()
}
$writer.WriteEndElement()

$writer.WriteStartElement('Connections')
foreach ($connection in $connections) {
    $writer.WriteStartElement('Connection')
    $writer.WriteAttributeString('pin', $connection.Pin)
    $writer.WriteAttributeString('siteNumber', $connection.SiteNumber)
    $writer.WriteAttributeString('instrument', $connection.Instrument)
    $writer.WriteAttributeString('channel', $connection.Channel)
    $writer.WriteEndElement()
}
foreach ($relayConnection in $relayConnections) {
    $writer.WriteStartElement('RelayConnection')
    $writer.WriteAttributeString('relay', $relayConnection.Relay)
    $writer.WriteAttributeString('siteNumber', $relayConnection.SiteNumber)
    $writer.WriteAttributeString('relayDriverModule', $relayConnection.RelayDriverModule)
    $writer.WriteAttributeString('controlLine', $relayConnection.ControlLine)
    $writer.WriteEndElement()
}
$writer.WriteEndElement()

$writer.WriteEndElement()
$writer.WriteEndDocument()
$writer.Flush()
$writer.Dispose()

Write-Output "Generated PinMap: $OutputPinmap"
Write-Output ("Pins: {0}" -f $pins.Count)
Write-Output ("Relays: {0}" -f $relayNames.Count)