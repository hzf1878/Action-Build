#!/usr/bin/env python3
"""为 FinaSU 的 AnyKernel3 anykernel.sh 注入 kernelsu.preinit=0。

FinaSU 的 preinit 会在 PID 1 执行 /system/bin/init 时用内嵌 runner 替换它，
在一加 /metadata 的挂载时序下会导致卡第一屏。编译期注入 KSU_NO_PREINIT 之外，
再在 boot cmdline 加 kernelsu.preinit=0 作为运行时保险。
"""
import re
import sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else "./AnyKernel3/anykernel.sh"
MARK = "kernelsu.preinit=0"

src = open(TARGET, encoding="utf-8").read()

if MARK in src:
    print("已存在 kernelsu.preinit=0，跳过")
    sys.exit(0)

# patch_cmdline 必须在 split_boot 之后、write_boot/flash_boot 之前
inject = (
    "split_boot\n"
    "# FinaSU: 关闭 preinit，避免替换 PID 1 导致卡第一屏\n"
    'patch_cmdline kernelsu.preinit "kernelsu.preinit=0"\n'
)

new, n = re.subn(r"^split_boot$", inject, src, count=1, flags=re.M)

if n != 1:
    print("❌ 未找到 split_boot 锚点，注入失败", file=sys.stderr)
    sys.exit(1)

open(TARGET, "w", encoding="utf-8").write(new)

# 校验
check = open(TARGET, encoding="utf-8").read()
if MARK not in check:
    print("❌ 写入后校验失败", file=sys.stderr)
    sys.exit(1)

print("✅ anykernel.sh 注入完成")
for i, line in enumerate(check.splitlines(), 1):
    if "split_boot" in line or "patch_cmdline" in line:
        print(f"  {i}: {line}")
