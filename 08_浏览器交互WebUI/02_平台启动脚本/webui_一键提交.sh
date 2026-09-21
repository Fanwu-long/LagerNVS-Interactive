#!/bin/bash
# 在平台 Web Shell (tradmin-02) 里整段粘贴执行
# 目标：A100 上启动 LagerNVS Browser WebUI → 本机 http://127.0.0.1:8765

set -euo pipefail
cd ~/lagernvs || { echo "缺少 ~/lagernvs，请先同步代码"; exit 1; }
mkdir -p logs

# 若还没有 sbatch，写一份
cat > run_interactive_live.sbatch <<'EOF'
#!/bin/bash
#SBATCH -J lager-webui
#SBATCH -p Students
#SBATCH --qos=qos_stu_default
#SBATCH --gres=gpu:A100:1
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 1:00:00
#SBATCH -o /home/scc/pb25612046/lagernvs/logs/webui-%j.out
#SBATCH -e /home/scc/pb25612046/lagernvs/logs/webui-%j.err

set -euo pipefail
export PYTHONUNBUFFERED=1
mkdir -p /home/scc/pb25612046/lagernvs/logs

module load miniconda/py312
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate lagernvs

cd /home/scc/pb25612046/lagernvs
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
if [ -z "${HF_TOKEN:-}" ] && [ -f "$HOME/.cache/huggingface/token" ]; then
  export HF_TOKEN="$(cat "$HOME/.cache/huggingface/token")"
fi

mkdir -p test_data/_raw_sidecars test_data/scene_a/_extra
mv -f test_data/scene_a_raw.jpg test_data/scene_b_raw.jpg test_data/_raw_sidecars/ 2>/dev/null || true
mv -f test_data/scene_a/view1.jpg test_data/scene_a/view2.jpg test_data/scene_a/_extra/ 2>/dev/null || true

echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-na} IP=$(hostname -I | awk '{print $1}')"
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"

exec python -u run_interactive_server.py \
  --scenes demo scene_a \
  --jpeg_quality 95 \
  --port 8765 \
  --bind 0.0.0.0
EOF

# 取消旧 WebUI 作业（可选）
squeue -u "$USER" | grep -E 'lager-webui|webui' || true

JOB=$(sbatch --parsable run_interactive_live.sbatch)
echo "SUBMITTED JOB=$JOB"
echo "等待分配 A100 …"
for i in $(seq 1 60); do
  st=$(squeue -j "$JOB" -h -o "%T" 2>/dev/null || echo "GONE")
  node=$(squeue -j "$JOB" -h -o "%N" 2>/dev/null || true)
  echo "[$i] state=$st node=$node"
  if [ "$st" = "RUNNING" ]; then
    break
  fi
  if [ "$st" = "GONE" ] || [ -z "$st" ]; then
    echo "作业已结束，看 logs/webui-$JOB.err"
    exit 1
  fi
  sleep 5
done

# 从日志解析 IP
IP=""
for i in $(seq 1 36); do
  if [ -f "logs/webui-$JOB.out" ]; then
    IP=$(grep -oE 'IP=[0-9.]+' "logs/webui-$JOB.out" | tail -1 | cut -d= -f2 || true)
    if grep -q "Listening\|serving\|WebSocket\|8765\|HOST=" "logs/webui-$JOB.out" 2>/dev/null; then
      break
    fi
  fi
  sleep 5
done

echo "======== 本机执行（PowerShell / 新终端）========"
if [ -n "$IP" ]; then
  echo "ssh -L 8765:${IP}:8765 -o ServerAliveInterval=30 ustc-lager"
  echo "然后浏览器打开: http://127.0.0.1:8765/"
  echo "门户自由视角: http://127.0.0.1:8766/07_交互式渲染演示/06_交互功能优化/free_camera.html 切 Live"
else
  echo "IP 尚未写出，请手动: tail -f ~/lagernvs/logs/webui-$JOB.out"
  echo "看到 IP=x.x.x.x 后本机: ssh -L 8765:<IP>:8765 ustc-lager"
fi
echo "JOB=$JOB  取消: scancel $JOB"
