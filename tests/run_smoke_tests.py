import subprocess, sys, os
from PIL import Image
import numpy as np

def run(cmd): print("+", " ".join(cmd)); subprocess.check_call(cmd)

def assert_png(path):
    assert os.path.exists(path), f"missing: {path}"
    img = Image.open(path).convert("RGB")
    w,h = img.size; assert w>100 and h>100, f"too small: {w}x{h}"
    arr = np.array(img); assert arr.std()>0.5, "image looks flat"

def main():
    run([sys.executable,"spiral.py","--csv","data/example.csv","--date-col","date","--value-col","value","--freq","M","--out","out_month.png"])
    assert_png("out_month.png")
    run([sys.executable,"spiral.py","--csv","data/example.csv","--date-col","date","--agg","count","--freq","W","--out","out_week.png"])
    assert_png("out_week.png")
    print("Smoke tests passed.")

if __name__=="__main__": main()
