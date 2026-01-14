# 🚀 Windows PowerShell 训练启动脚本
# 用法：
#   .\train.ps1                    # 交互式选择角色
#   .\train.ps1 linzhi             # 直接训练指定角色
#   .\train.ps1 --menu             # 显示完整菜单（推荐）
#   .\train.ps1 --list             # 列出所有配置
#   .\train.ps1 --scan             # 扫描数据集
#   .\train.ps1 --cache            # 检查模型缓存状态
#   .\train.ps1 linzhi --ollama    # 训练并导出到Ollama

# 设置UTF-8编码以支持emoji和中文
chcp 65001 | Out-Null  # 设置控制台代码页为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::GetEncoding(65001)
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

# 设置Python环境变量，确保Python输出使用UTF-8编码
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# 切换到脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 函数：检测系统CUDA版本
function Get-SystemCUDAVersion {
    $cudaVersion = $null
    
    # 方法1: 通过nvidia-smi检测CUDA版本（从完整输出中提取）
    try {
        $nvidiaSmiOutput = nvidia-smi 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0 -and $nvidiaSmiOutput) {
            # 从输出中查找 "CUDA Version: X.X" 或 "CUDA Version: X.X"
            $match = [regex]::Match($nvidiaSmiOutput, "CUDA Version:\s*(\d+\.\d+)")
            if ($match.Success) {
                $cudaVersion = $match.Groups[1].Value
            }
        }
    } catch {
        # nvidia-smi不可用，继续尝试其他方法
    }
    
    # 方法2: 通过nvcc检测
    if (-not $cudaVersion) {
        try {
            $nvccVersion = nvcc --version 2>&1 | Out-String
            $match = [regex]::Match($nvccVersion, "release (\d+\.\d+)")
            if ($match.Success) {
                $cudaVersion = $match.Groups[1].Value
            }
        } catch {
            # nvcc不可用
        }
    }
    
    return $cudaVersion
}

# 函数：根据CUDA版本选择PyTorch安装命令
function Get-PyTorchInstallCommand {
    param([string]$cudaVersion)
    
    if (-not $cudaVersion) {
        return $null
    }
    
    # 提取主版本号（如 "12.3" -> "12.3"）
    if ($cudaVersion -match "^(\d+\.\d+)") {
        $majorMinor = $matches[1]
    } else {
        return $null
    }
    
    # CUDA版本映射到PyTorch索引
    $versionMap = @{
        "12.4" = "cu124"
        "12.3" = "cu124"  # 12.3使用12.4的wheel（兼容）
        "12.2" = "cu121"  # 12.2使用12.1的wheel（兼容）
        "12.1" = "cu121"
        "12.0" = "cu121"  # 12.0使用12.1的wheel（兼容）
        "11.8" = "cu118"
        "11.7" = "cu118"  # 11.7使用11.8的wheel（兼容）
    }
    
    # 精确匹配
    if ($versionMap.ContainsKey($majorMinor)) {
        $wheelVersion = $versionMap[$majorMinor]
        return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/$wheelVersion"
    }
    
    # 模糊匹配（取最接近的版本）
    $versionParts = $majorMinor.Split('.')
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    
    if ($major -ge 12) {
        if ($minor -ge 3) {
            # CUDA 12.3及以上使用cu124
            return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124"
        } elseif ($minor -ge 1) {
            # CUDA 12.1-12.2使用cu121
            return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
        }
    } elseif ($major -eq 11 -and $minor -ge 7) {
        return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
    }
    
    return $null
}

# 函数：检查GPU设备并自动安装CUDA PyTorch
function Check-GPU-Device {
    Write-Host ""
    Write-Host "Checking GPU device..." -ForegroundColor Cyan
    
    $checkScript = @"
import torch
print('PyTorch:', torch.__version__)
print('CUDA_AVAILABLE:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('CUDA_VERSION:', torch.version.cuda)
    print('GPU_COUNT:', torch.cuda.device_count())
    print('GPU_NAME:', torch.cuda.get_device_name(0))
"@
    
    $checkScript | Out-File -FilePath "$env:TEMP\check_gpu.py" -Encoding utf8
    $pythonOutput = python "$env:TEMP\check_gpu.py" 2>&1
    Remove-Item "$env:TEMP\check_gpu.py" -ErrorAction SilentlyContinue
    
    if ($LASTEXITCODE -eq 0) {
        $torchVersion = ($pythonOutput | Select-String "PyTorch: (.+)").Matches.Groups[1].Value
        $cudaAvailable = ($pythonOutput | Select-String "CUDA_AVAILABLE: (.+)").Matches.Groups[1].Value
        
        if ($torchVersion -match "\+cpu" -or $cudaAvailable -eq "False") {
            # 检查是否已经跳过安装（避免每次都询问）
            $skipFile = ".venv\.skip_cuda_install"
            if (Test-Path $skipFile) {
                Write-Host ""
                Write-Host "Note: CPU-only PyTorch detected. GPU acceleration not available." -ForegroundColor Yellow
                Write-Host "To enable GPU, delete $skipFile and run the script again, then choose to install CUDA PyTorch." -ForegroundColor Gray
                return
            }
            
            Write-Host ""
            Write-Host "WARNING: CPU-only PyTorch detected. Training will be SLOW!" -ForegroundColor Yellow
            Write-Host "Current PyTorch: $torchVersion" -ForegroundColor Yellow
            Write-Host ""
            
            # 检测系统CUDA版本
            Write-Host "Detecting system CUDA version..." -ForegroundColor Cyan
            $systemCudaVersion = Get-SystemCUDAVersion
            
            if ($systemCudaVersion) {
                Write-Host "System CUDA version detected: $systemCudaVersion" -ForegroundColor Green
                $installCmd = Get-PyTorchInstallCommand -cudaVersion $systemCudaVersion
                
                if ($installCmd) {
                    Write-Host ""
                    Write-Host "Auto-install CUDA-enabled PyTorch for CUDA $systemCudaVersion?" -ForegroundColor Yellow
                    Write-Host "Command: $installCmd" -ForegroundColor Gray
                    Write-Host ""
                    Write-Host "Install now? (Y/n): " -NoNewline -ForegroundColor Yellow
                    $response = Read-Host
                    
                    if ($response -notmatch "^[nN]") {
                        Write-Host ""
                        Write-Host "Installing CUDA PyTorch (this may take a few minutes)..." -ForegroundColor Yellow
                        Invoke-Expression $installCmd
                        
                        if ($LASTEXITCODE -eq 0) {
                            Write-Host "CUDA PyTorch installed successfully!" -ForegroundColor Green
                            Write-Host "Please restart the script to use GPU acceleration." -ForegroundColor Cyan
                            Write-Host ""
                            Write-Host "Press Enter to exit..." -NoNewline
                            Read-Host
                            exit 0
                        } else {
                            Write-Host "Installation failed. Please install manually:" -ForegroundColor Red
                            Write-Host "  $installCmd" -ForegroundColor Gray
                            Write-Host ""
                            Write-Host "Continue with CPU training? (y/N): " -NoNewline -ForegroundColor Yellow
                            $response = Read-Host
                            if ($response -notmatch "^[yY]") {
                                exit 0
                            }
                        }
                    } else {
                        Write-Host ""
                        Write-Host "Skipping auto-install. Continue with CPU training? (y/N): " -NoNewline -ForegroundColor Yellow
                        $response = Read-Host
                        if ($response -notmatch "^[yY]") {
                            exit 0
                        } else {
                            # 创建标记文件，下次不再询问
                            "" | Out-File -FilePath ".venv\.skip_cuda_install" -Encoding utf8 -Force
                            Write-Host "Note: Skipping CUDA install. This prompt won't appear again." -ForegroundColor Gray
                            Write-Host "To re-enable, delete .venv\.skip_cuda_install" -ForegroundColor Gray
                        }
                    }
                } else {
                    Write-Host "Could not determine PyTorch installation command for CUDA $systemCudaVersion" -ForegroundColor Yellow
                    Write-Host "Please visit https://pytorch.org/get-started/locally/ for installation instructions" -ForegroundColor Cyan
                    Write-Host ""
                    Write-Host "Continue with CPU training? (y/N): " -NoNewline -ForegroundColor Yellow
                    $response = Read-Host
                    if ($response -notmatch "^[yY]") {
                        exit 0
                    } else {
                        # 创建标记文件，下次不再询问
                        "" | Out-File -FilePath ".venv\.skip_cuda_install" -Encoding utf8 -Force
                    }
                }
            } else {
                Write-Host "Could not detect CUDA version. Please check manually:" -ForegroundColor Yellow
                Write-Host "  nvidia-smi" -ForegroundColor Gray
                Write-Host ""
                Write-Host "Then install CUDA PyTorch from: https://pytorch.org/get-started/locally/" -ForegroundColor Cyan
                Write-Host ""
                Write-Host "Continue with CPU training? (y/N): " -NoNewline -ForegroundColor Yellow
                $response = Read-Host
                if ($response -notmatch "^[yY]") {
                    exit 0
                } else {
                    # 创建标记文件，下次不再询问
                    "" | Out-File -FilePath ".venv\.skip_cuda_install" -Encoding utf8 -Force
                    Write-Host "Note: Skipping CUDA install. This prompt won't appear again." -ForegroundColor Gray
                    Write-Host "To re-enable, delete .venv\.skip_cuda_install" -ForegroundColor Gray
                }
            }
        } else {
            $cudaVersion = ($pythonOutput | Select-String "CUDA_VERSION: (.+)").Matches.Groups[1].Value
            $gpuName = ($pythonOutput | Select-String "GPU_NAME: (.+)").Matches.Groups[1].Value
            Write-Host "GPU detected: $gpuName (CUDA $cudaVersion)" -ForegroundColor Green
        }
    }
}

# 函数：检查并安装依赖
function Check-AndInstall-Dependencies {
    Write-Host ""
    Write-Host "Checking dependencies..." -ForegroundColor Cyan
    
    # 检查虚拟环境
    if (-not (Test-Path ".venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to create virtual environment. Please check if Python is installed correctly." -ForegroundColor Red
            exit 1
        }
        Write-Host "Virtual environment created successfully" -ForegroundColor Green
    }
    
    # 激活虚拟环境
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
    
    # 检查关键依赖
    $requiredPackages = @(
        @{Name="torch"; Import="torch"},
        @{Name="transformers"; Import="transformers"},
        @{Name="peft"; Import="peft"},
        @{Name="trl"; Import="trl"},
        @{Name="datasets"; Import="datasets"},
        @{Name="yaml"; Import="yaml"}
    )
    $missingPackages = @()
    
    foreach ($pkg in $requiredPackages) {
        $null = python -c "import $($pkg.Import)" 2>&1
        if ($LASTEXITCODE -ne 0) {
            $missingPackages += $pkg.Name
        }
    }
    
    # 如果有缺失的依赖，安装requirements.txt
    if ($missingPackages.Count -gt 0 -or -not (Test-Path ".venv\.deps_installed")) {
        Write-Host ""
        Write-Host "Missing dependencies detected, installing..." -ForegroundColor Yellow
        if ($missingPackages.Count -gt 0) {
            Write-Host "Missing packages: $($missingPackages -join ', ')" -ForegroundColor Yellow
        }
        
        if (Test-Path "requirements.txt") {
            Write-Host "Installing dependencies from requirements.txt (this may take a few minutes)..." -ForegroundColor Yellow
            python -m pip install --upgrade pip -q
            python -m pip install -r requirements.txt
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Dependencies installed successfully" -ForegroundColor Green
                # 创建标记文件
                "" | Out-File -FilePath ".venv\.deps_installed" -Encoding utf8
            } else {
                Write-Host "Failed to install dependencies. Please check your network or run manually: pip install -r requirements.txt" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "requirements.txt file not found" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "All dependencies are installed" -ForegroundColor Green
    }
}

# 检查并安装依赖（仅在非帮助命令时）
$skipCheck = $false
foreach ($arg in $args) {
    if ($arg -eq "--help" -or $arg -eq "-h" -or $arg -eq "--version") {
        $skipCheck = $true
        break
    }
}

if (-not $skipCheck) {
    Check-AndInstall-Dependencies
    Check-GPU-Device

    # 检查并安装 questionary（用于箭头选择菜单）
    $null = python -c "import questionary" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Installing questionary for better menu experience..." -ForegroundColor Cyan
        python -m pip install questionary -q
        if ($LASTEXITCODE -eq 0) {
            Write-Host "questionary installed successfully!" -ForegroundColor Green
            Write-Host ""
        } else {
            Write-Host "questionary installation failed, will use traditional number input" -ForegroundColor Yellow
            Write-Host ""
        }
    }
}

# 运行智能训练脚本，传递所有参数
python smart_train.py $args

