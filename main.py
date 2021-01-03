import math
import random
import time
from kubernetes import client, config
from sympy import *
import yaml

'''
输入：无
输出：无
描述：每隔120s去检测负载的变化
     若负载有变化，则推荐一个新的方案
'''
_YAML_FILE_NAME = 'arg.yaml'


def decide(loadfromtxt, rpsfromtxt, limitfromtxt, arg):
    interval = arg['interval']
    rps_per_pod = arg['pod_rps']
    limit = arg['pod_limit']

    current_num = 1
    loadcount = 0
    while True:
        # 获取最新的负载
        load = loadfromtxt[loadcount]
        # load = random.randint(50,300)

        if 1.0 * load / (current_num * rps_per_pod) > 0.9:
            while True:
                current_num = current_num + 1
                if 1.0 * load / (current_num * rps_per_pod) <= 0.9:
                    break
            pass
        pass
        if 1.0 * load / (current_num * rps_per_pod) < 0.4:
            while True:
                if current_num > 1:
                    current_num = current_num - 1
                    if 1.0 * load / (current_num * rps_per_pod) >= 0.4:
                        break
                    pass
                else:
                    break
            pass
        pass

        res_cost = math.ceil(current_num*limit/1000)*arg['interval']*arg['p_cpu']
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        print("current index: %d " % loadcount)
        print("load: %d " % load)
        print("pod_num: %d " % current_num)
        print("res_cost: %f " % res_cost)
        print("*" * 30)
        f = open('adaptive_result.txt', 'a')
        f.write(time.strftime("\n%Y-%m-%d %H:%M:%S\n", time.localtime()))
        f.write("current index: %d\n" % loadcount)
        f.write("load : %d\n" % load)
        f.write("pod_num : %d\n" % current_num)
        f.write("res_cost: %f\n" % res_cost)
        f.write("*" * 50)
        f.close()
        # execute(current_num,limit,arg)
        # time.sleep(interval)
        loadcount = loadcount + 1
        if loadcount >= len(loadfromtxt):
            print("伸缩测试结束")
            break
        pass
    pass


'''
输入：pod的个数、request(limit和request相同)
输出：无
描述：执行组合式伸缩的方案
'''


def execute(num_pod, limit_pod, arg):
    config.load_kube_config()
    api_instance = client.AppsV1Api()
    deployment = arg['deployment']
    namespace = arg['namespace']
    deployobj = api_instance.read_namespaced_deployment(deployment, namespace)

    # 执行伸缩方案
    recommend_cpu_requests = int(limit_pod)
    # recommend_mem_requests = 200
    recommend_cpu_limits = int(limit_pod)
    # recommend_mem_limits = 200
    recommend_requests = {
        'cpu': str(recommend_cpu_requests) + 'm',
        # 'memory': str(recommend_mem_requests) + 'Mi'
    }
    recommend_limits = {
        'cpu': str(recommend_cpu_limits) + 'm',
        # 'memory': str(recommend_mem_limits) + 'Mi'
    }
    deployobj.spec.template.spec.containers[0].resources.limits.update(recommend_limits)
    deployobj.spec.template.spec.containers[0].resources.requests.update(recommend_requests)
    deployobj.spec.replicas = num_pod
    api_instance.replace_namespaced_deployment(deployment, namespace, deployobj)


def prepare():
    loadfromtxt = []

    rpsfromtxt = []

    limitfromtxt = []

    file = 'load.txt'
    with open(file, 'r') as file_to_read:
        while True:
            lines = file_to_read.readline()  # 整行读取数据
            if not lines:
                break
                pass
            tmp = int(lines.strip('\n'))
            loadfromtxt.append(tmp)  # 添加新读取的数据
            pass
    pass
    print(loadfromtxt)

    filename = 'data.txt'
    with open(filename, 'r') as file_to_read:
        while True:
            lines = file_to_read.readline()  # 整行读取数据
            if not lines:
                break
                pass
            tmp_limit, tmp_rps = [float(i) for i in lines.split()]  # 将整行数据分割处理，如果分割符是空格，括号里就不用传入参数，如果是逗号， 则传入‘，'字符。
            # print(tmp_limit,tmp_rps)
            rpsfromtxt.append(tmp_rps)
            limitfromtxt.append(tmp_limit)
    pass
    print(limitfromtxt)
    print(rpsfromtxt)
    return loadfromtxt, rpsfromtxt, limitfromtxt


def main():
    with open(_YAML_FILE_NAME) as f:
        arg = yaml.load(f, Loader=yaml.FullLoader)
    loadfromtxt, rpsfromtxt, limitfromtxt = prepare()
    decide(loadfromtxt, rpsfromtxt, limitfromtxt, arg)

    f = open('adaptive_result.txt', 'a')
    f.write("\nend of the test\n\n\n")
    f.close()


if __name__ == '__main__':
    main()
