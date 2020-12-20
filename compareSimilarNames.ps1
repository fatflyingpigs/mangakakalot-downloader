

$ScriptDirectory = Split-Path $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDirectory NaturalSort.ps1)

# Get-ChildItem $root -Directory | `
$i = ""
$iDate = ""
$j = ""
$jDate = ""
$dir = ""
# Get-ChildItem -Directory | `
# Get-ChildItem 
Get-ChildItem -Directory | ForEach-Object {
Write-Host "Moving next dir: " $_.FullName -ForegroundColor Green
$subdir = ls $_.FullName
Sort-Naturally -Array $subdir |
	ForEach-Object {
		# Write-Host "    i: " $i "j: " $j "iDate: " $iDate "jDate: " $jDate
		if($dir -ne $_.Directory.Name){
			$dir = $_.Directory.Name
			$j = $_.Name
			$jDate = $_.CreationTime
			# Write-Host "Moving next dir: " $dir
			return
		}

		$i = $_.Name
		$iDate = $_.CreationTime
		$min = [Math]::Min($i.length, $j.length)
		$smaller = if ($i.length -eq $min) {'i'} else {'j'}
		$min -= 4 #remove the extension

		if($j.length -le 12){ # "Chapter .cbz".length == 12
			# Write-Host "`ti: " + $i + "\tj: " + $j
			$j = $_.Name
			$jDate = $_.CreationTime
			return
		}

		# Write-Host "`tmin: " $min
		# Write-Host "`ti: " $i "j: " $j
		# Write-Host "`ti: " $i.length "j: " $j.length
		# Write-Host "`tiDate: " $iDate "jDate: " $jDate
		# Write-Host "`ti: " $i.SubString(0,$min) "j: " $j.SubString(0,$min)

		if(-not (Compare-Object $i.SubString(0,$min) $j.SubString(0,$min))){
			# Write-Host "strings are equal"
			# Write-Host "i: " $i.SubString(0,$min) "j: " $j.SubString(0,$min)
			# Write-Host "i: " $iDate "j: " $jDate
			$testForC = $min + 2
			if($smaller -eq 'i') { # check if it's a Chapter 2.5, 4.1, 4.2, etc.
				if($j.Substring($testForC,1) -ne 'c'){
					Write-Host "`ti smaller: " $i -ForegroundColor Yellow
					Write-Host "`tj larger : " $j -ForegroundColor Yellow
					$j = $_.Name
					$jDate = $_.CreationTime
					return
				}
			}else{ # $smaller -eq 'j'
				if($i.Substring($testForC,1) -ne 'c'){
					Write-Host "`ti larger : " $i -ForegroundColor Yellow
					Write-Host "`tj smaller: " $j -ForegroundColor Yellow
					$j = $_.Name
					$jDate = $_.CreationTime
					return
				}
			}

			if ($iDate -lt $jDate){ # i is older, keep j
				Write-Host "`ti older, keep j: " $j -ForegroundColor Green
			}else{ # j is older, keep i
				Write-Host "`tj older, keep i: " $i -ForegroundColor Green
			}
		}else{
			# Write-Host "`tstrings are different"
		}

		$j = $_.Name
		$jDate = $_.CreationTime
	}
}