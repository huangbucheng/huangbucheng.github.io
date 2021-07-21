# 基于kubernetes的任务调度系统设计

## 简介
在一个基于编程的游戏平台项目中，用户提交的python代码由后台调度运行。其中设计服务器端运行用户代码，运行环境的安全和隔离显得尤为重要。

在项目初期，基于项目时间需求考虑，基于Mysql做任务调度管理和cgroup沙箱隔离上线了一个初级版本。该版本运行稳定，然而被公司安全部门扫描发现一些安全问题，由于沙箱环境的权限控制粗糙，并且未和后台业务服务器做隔离，是的用户代码可以获取到服务器上的业务信息。

项目之初也提出过基于kubernetes的方案，在安全风险的推动下，使用kubernets对任务调度系统进行了全面改造。
本文从以下几个主要方面阐述一下新方案的要点：
- kubernetes Job对任务的封装；
- kubernets NetworkPolicy 对Job网络环境的控制；
- 用户代码运行环境裁剪；

## kubernetes Job对任务的封装
### Job封装的scope
Job的封装遵循单一职责原则（SRP），因为Job中会运行用户代码，本着外部不可信原则，Job应与其他业务逻辑、运行环境做好切割。

游戏平台调度的任务是运行用户代码参与本地游戏，最后输出游戏结果和replay文件。因此Job的scope设定为游戏运行的最小需求，并且不依赖数据库、外部网络、外部服务等，最终产出物通过pv输出。

定义好Job的scope之后，就可以为Job的Pod构建基础镜像了，基础镜像需要能够满足游戏的运行，但又不能暴露非必要的信息和能力。

### Job Api
部署Job通过kuberbets API Server编程实现，kubernetes.io提供了文档说明：[编程方式访问 API](https://kubernetes.io/zh/docs/tasks/administer-cluster/access-cluster-api/#%E7%BC%96%E7%A8%8B%E6%96%B9%E5%BC%8F%E8%AE%BF%E9%97%AE-api)

API客户端初始化需要kubeconfig文件 定位和验证 API Server服务器，在腾讯云容器服务 TKE 中，kubeconfig文件在集群“基本信息”->“集群APIServer信息”中可以获取。同时还需要配置API Server域名的Host，例如：`sudo sed -i '$a 172.16.0.1 cls-xxxxx.ccs.tencent-cloud.com' /etc/hosts` 。

运用面向对象的方法，基于client-go封装一个k8sclient，然后在k8sclient上封装一下CreateJob、GetJob、DeleteJob接口:
```go
package k8sclient

import (
    "context"
    "fmt"
    "time"

    batchv1 "k8s.io/api/batch/v1"
    v1 "k8s.io/api/core/v1"
    "k8s.io/apimachinery/pkg/api/errors"
    "k8s.io/apimachinery/pkg/api/resource"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/rest"
    "k8s.io/client-go/tools/clientcmd"
    "k8s.io/utils/pointer"
)

type KubeClient struct {
    kubeconfigPath string
    cs             *kubernetes.Clientset
}

func (c *KubeClient) WithKubeConfig(kubeconfigPath string) error {
    // uses the current context in kubeconfig
    // path-to-kubeconfig -- for example, /root/.kube/config
    config, err := clientcmd.BuildConfigFromFlags("", kubeconfigPath)
    if err != nil {
            return err
    }

    // creates the clientset
    c.cs, err = kubernetes.NewForConfig(config)
    if err != nil {
            return err
    }

    return nil
}
```

#### CreateJob
调度系统调度一个任务时，对应的行为是创建一个Job：
```go
type JobRequest struct {
    Namespace               string
    JobName                 string
    Image                   string
    CpuRequest              string
    MemoryRequest           string
    CpuLimit                string
    MemoryLimit             string
    Mounts                  []VolumeMount
    Envs                    map[string]string
    TTLSecondsAfterFinished int32
}
type VolumeMount struct {
    Name      string
    MountPath string
    HostPath  string
}

func (c *KubeClient) CreateJob(ctx context.Context, req *JobRequest) (
    *batchv1.Job, error) {
    var volumes []v1.Volume
    var mounts []v1.VolumeMount
    volumes, mounts = genHostPathVolumeMount(req.Mounts)

    jobsClient := c.cs.BatchV1().Jobs(req.Namespace)
    job := &batchv1.Job{
        ObjectMeta: metav1.ObjectMeta{
            Name:      req.JobName,
            Namespace: req.Namespace,
        },
        Spec: batchv1.JobSpec{
            BackoffLimit:            pointer.Int32Ptr(1),
            TTLSecondsAfterFinished: pointer.Int32Ptr(req.TTLSecondsAfterFinished),
            Template: v1.PodTemplateSpec{
                Spec: v1.PodSpec{
                    RestartPolicy: "Never",
                    Containers: []v1.Container{
                        {
                            Name:  "main",
                            Image: req.Image,
                            Env:   genEnvs(req.Envs),
                            //Command: []string{"sleep"},
                            //Args:    []string{"10000"},
                            SecurityContext: &v1.SecurityContext{
                                Privileged:               pointer.BoolPtr(false),
                                AllowPrivilegeEscalation: pointer.BoolPtr(false),
                                ReadOnlyRootFilesystem:   pointer.BoolPtr(true),
                            },
                            Resources: genResourceRequirements(req.CpuRequest, req.MemoryRequest),
                            VolumeMounts: mounts,
                        },
                    },
                    Volumes:          volumes,
                    ImagePullSecrets: []v1.LocalObjectReference{{Name: "qcloudregistrykey"}},
                },
            },
        },
    }

    return jobsClient.Create(ctx, job, metav1.CreateOptions{})
}
```
`JobRequest`定义了创建Job的必要参数：
- Namespace: Job的命名空间
- JobName: Job名称，任务重试时，重名会导致创建Job失败，需要根据需要处理。
- Image: 镜像地址
- CpuRequest: 例，500m
- MemoryRequest: 例，512Mi
- CpuLimit: 例，500m
- MemoryLimit: 例，512Mi
- Mounts: 磁盘挂载信息
- Envs: 环境变量
- TTLSecondsAfterFinished: 自动清理已结束Job（Completed 或 Finished）

#### GetJob
调度系统创建Job之后，通过轮询Job状态检查任务是否执行完成。
```go
func (c *KubeClient) GetJob(ctx context.Context, namespace, jobname string) (*batchv1.Job, error) {
    return c.cs.BatchV1().Jobs(namespace).Get(ctx, jobname, metav1.GetOptions{})
}
```

#### DeleteJob
调度系统处理完已完成的Job之后，主动删除Job：
```go
func (c *KubeClient) DeleteJob(ctx context.Context, namespace, jobname string) error {
    propagationPolicy := metav1.DeletePropagationBackground
    return c.cs.BatchV1().Jobs(namespace).Delete(ctx, jobname, metav1.DeleteOptions{PropagationPolicy: &propagationPolicy})
}
```

### Job容器安全上下文
在创建Job封装接口中，根据业务场景固定了安全性上下文 `SecurityContext` 的设置：
- Privileged: false 以非特权模式运行
- AllowPrivilegeEscalation: 控制进程是否可以获得超出其父进程的特权
- ReadOnlyRootFilesystem：以只读方式加载容器的根文件系统，防止用户代码上传写入恶意文件

### Job资源回收销毁
通过 `TTLSecondsAfterFinished` 可以自动清理已结束的Job，但在TKE中，该字段貌似不生效。

## kubernets NetworkPolicy 对Job网络环境的控制
kubernetes.io：*NetworkPolicy 是一种以应用为中心的结构，允许你设置如何允许 Pod 与网络上的各类网络“实体” 通信。*

基于业务场景，用户代码只需要在本地执行游戏逻辑处理，不需要访问其他网络资源，因此我们选择禁掉所有的Job的网络出口。

通过将所有Job至于一个独立的kubernetes namespace内，然后创建一个NetworkPolicy来阻止该namespace下pod的外出网络请求：
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: np-job
  namespace: isolate-job
spec:
  podSelector: {}
  policyTypes:
  - Egress
```
运行 `kubectl apply -f np.yaml` 创建成功后，isolate-job namespace下的Job就不能访问其他Pod、Node节点和公网了。

腾讯云容器服务 TKE 中，需要为TKE集群安装NetworkPolicy组件，可参考官方指引 [使用 Network Policy 进行网络访问控制](https://cloud.tencent.com/document/product/457/19793) 。

## 用户代码运行环境裁剪
用户代码运行环境应遵循最小可用原则，非必需的库、命令行工具都可以裁剪掉。
一般可以把 `ping`, `telnet`, `netstat`, `ss`, `ifconfig`, `nmap`, `lsof`, `nc`, `tcpdump`, `curl`, `wget` 等工具都删除掉。