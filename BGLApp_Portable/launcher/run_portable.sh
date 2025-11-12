#!/bin/bash
cd "$(dirname "$0")"
python3 run_portable.py
if [ $? -ne 0 ]; then
  echo "فشل تشغيل التطبيق"
  read -p "اضغط Enter للمتابعة..."
fi
