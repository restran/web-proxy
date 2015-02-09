# 基于 Tornado 实现的 Web 站点反向代理

因为一个奇怪的需求，使用 Python 和 Tornado 框架实现了一个 Web 站点的反向代理。实现的功能是这样：

1. 假设这个反向代理网站的地址是 http://www.example.com
2. 访问 http://www.example.com/.site.backend_site0/，访问的是 backend_site0，这个网站可以是部署在内网的某个站点（外网当然也是可以）。
3. 访问 http://www.example.com/.site.backend_site1/，访问另外一个站点 backend_site1

怎么通过一个公共的站点反向代理访问后端的多个站点，当时的讨论帖在[这里][1]，我采用的是：

1. 在url中添加前缀 `.site.`，第一次访问的时候使用 http://www.example.com/.site.backend_site/
2. 服务端识别出请求的后端站点 `backend_site` 后，会设置 Cookie，`.site = backend_site`，后续的访问会根据Cookie来识别出来。
3. 当访问另外一个网站 http://www.example.com/.site.backend_site1/，这时候，服务端会清除旧的 Cookie，并设置新的 Cookie，`.site = backend_site1`，这样就切换到新的站点 `backend_site1`
4. 启用页面内容替换，保证页面内的内网IP地址转换成反向代理的地址。例如后端站点 backend_site0 的地址是 http://10.1.2.3/，页面内有链接 http://10.1.2.3/img/a.png，将其替换成  /.site.backend_site0/img/a.png


## 环境需求

Python 2.7
Tornado 4.0


## 所代理的后端网站注意事项

1. url 的前缀不应出现 /.site. 
    由于反向代理采用url前缀来区分后端网站，如 /.site.example/，表示后端站点example。
    例如以下为禁用的url：
    /.site./
    /.site.example/
    /.site.example/user/login/

2. cookies 中不应出现以 .site 命名的 cookie 值，这个 cookie 是用来标识当前访问的后端站点

## CentOS 7.0 部署

Tornado 的部署可以参照[这里][2]的教程。通过启动多个 Tornado 实例，来避免调用到同步函数块，导致阻塞住，无法响应其他用户的请求。使用 supervisor 来启动 Tornado Server，并使用 Nginx 作为 Web 服务器，反向代理后端的这些 Tornado 实例。


### 修改配置文件 settings.py

```python
# 转发到后端需要代理的网站的地址列表
forward_list = {
    "baidu": BackendSite('baidu', 'http://www.baidu.com', 'www.baidu.com', []),
    "douban": BackendSite('douban', 'http://www.douban.com', 'www.douban.com', [
        # 使用正则表达式替换页面内容，参数分别是
        # 需要替换的URI的正则表达式，源字符串的正则表达式，替换后的字符串 
        SubsFilterRules('.', r'http://www\.douban\.com', '/.site.douban'),
        SubsFilterRules('.', r'http://img3\.douban\.com', '/.site.img3.douban'),
        SubsFilterRules('.', r'http://img5\.douban\.com', '/.site.img5.douban'),
    ]),
    "img3.douban": BackendSite('douban', 'http://img3.douban.com', 'img3.douban.com', []),
    "img5.douban": BackendSite('douban', 'http://img5.douban.com', 'img5.douban.com', []),
}
```

### 使用 supervisor 启动 Tornado Server

设置配置文件

    vim /etc/supervisord.conf

输入如下信息

```
[program:tornado_server_9001]
command=python /home/python/web_proxy/proxy.py --port=9001
directory=/home/python/web_proxy
autorestart=true
redirect_stderr=true
stdout_logfile = /var/log/supervisord/web_proxy.log

[program:tornado_server_9002]
command=python /home/python/web_proxy/proxy.py --port=9002
directory=/home/python/web_proxy
autorestart=true
redirect_stderr=true
stdout_logfile = /var/log/supervisord/web_proxy.log

[program:tornado_server_9003]
command=python /home/python/web_proxy/proxy.py --port=9003
directory=/home/python/web_proxy
autorestart=true
redirect_stderr=true
stdout_logfile = /var/log/supervisord/web_proxy.log
```

重新加载配置文件

    supervisorctl reload

重新启动所有程序

    sudo supervisorctl restart all

### 配置 nginx

添加 nginx 配置文件

    vim /etc/nginx/conf.d/web_proxy.conf

输入如下配置信息

```
upstream tornadoes {
    server 127.0.0.1:9001;
    server 127.0.0.1:9002;
    server 127.0.0.1:9003;
}

server {
    listen 9000;
    server_name your_server_name; # 例如输入服务器IP
    gzip on;
    # 设置允许压缩的页面最小字节数，页面字节数从header头得content-length中进行获取。默认值是0，不管页面多大都压缩。建议设置成大于1k的字节数，小于1k可能会越压越大。
    gzip_min_length 1000;
    gzip_buffers 4 16k;
    gzip_http_version 1.1;
    # 1~9，默认为1，数值越大，压缩率越高，CPU占用越多，时间越久
    gzip_comp_level 3;
    gzip_vary on;
    # 禁用对 IE 6 使用 gzip 压缩
    gzip_disable "MSIE [1-6]\.";
    gzip_types text/plain text/html text/css application/x-javascript text/xml application/xml application/xml+rss text/javascript application/json;

    ## Individual nginx logs
    access_log  /var/log/nginx/web_proxy_access.log;
    error_log   /var/log/nginx/web_proxy_error.log;

    location / {
        proxy_pass_header Server;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Scheme $scheme;
        proxy_pass http://tornadoes;
    }
}
```

重启 nginx

    service nginx restart


## todo
URL 访问控制，访问列表


  [1]: http://www.v2ex.com/t/146552#reply24
  [2]: http://mirrors.segmentfault.com/itt2zh/ch8.html