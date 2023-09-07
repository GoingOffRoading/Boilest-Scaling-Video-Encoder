==== FFPROBE ====

ffmpeg -hide_banner -loglevel 16 -stats -r 24 -i newtest.mkv -r 24 -i newtestsrtlaopus.mkv -lavfi libvmaf="n_threads=20:n_subsample=10" -f null -

====

OPUS Audio:
ffmpeg -hide_banner -loglevel 16 -stats -i INPUT.mkv -c:v libsvtav1 -crf 20 -preset 5 -g 240 -pix_fmt yuv420p10le -c:s srt -c:a libopus OUTPUT.mkv

===


hvec nvec text:
ffmpeg -i test.mkv -c:v hevc_nvenc -crf 20 -keyint 240 -pix_fmt yuv420p10le test_nvec_crf20.mkv


---




for filename in os.listdir(path):
    if (filename.endswith(".mp4")): #or .avi, .mpeg, whatever.
        os.system(f'ffmpeg -i {filename} -f image2 -vf fps=fps=1 output%d.png')
    else:
        continue






https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/


 nodeSelector:
    disktype: ssd


    kubectl label nodes <your-node-name> disktype=ssd



    https://kubernetes.io/docs/tasks/configure-pod-container/assign-pods-nodes/





    https://www.geeksforgeeks.org/how-to-run-bash-script-in-python/





    https://github.com/njhowell/python-videoencoder/blob/master/README.md


https://medium.com/kubernetes-tutorials/learn-how-to-assign-pods-to-nodes-in-kubernetes-using-nodeselector-and-affinity-features-e62c437f3cf8



https://medium.com/@tanchinhiong/separating-celery-application-and-worker-in-docker-containers-f70fedb1ba6d



https://docs.celeryq.dev/en/stable/userguide/monitoring.html
