import os
import shutil

os.chdir("/home/boggsj/Coding/research/Soar")
build_result = os.system("python scons/scons.py all --dbg --use-opencv")

if build_result != 0:
    print(f"Soar build failed: {build_result}")
    quit(build_result)
else:
    print("Soar build succeeded")

shutil.copy("out/libSoar.so", "/home/boggsj/anaconda3/envs/mine_env/lib/python3.9/site-packages")
shutil.copy("out/Python_sml_ClientInterface.py", "/home/boggsj/anaconda3/envs/mine_env/lib/python3.9/site-packages")
shutil.copy("out/_Python_sml_ClientInterface.so", "/home/boggsj/anaconda3/envs/mine_env/lib/python3.9/site-packages")