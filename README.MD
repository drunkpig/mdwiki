
## mdwiki介绍
一句话概括下mdwiki特点：
```bash
一条命令把一个目录内的markdown文档构建成个人博客展示在github上，结合travis-ci实现全自动发布。
您无需在本机配置任何东西，无需安装nodejs, python等，您只需要在本机编辑markdown，然后push到您的github仓库就OK了。

```



## 使用手册

#### 步骤1. 创建博客github仓库

创建一个空的仓库，切换到分支`source`, 目的是让`master`分支放编译好的博客。

仓库里建个目录post, post里以日期为目录，目录里写md博客，推荐typora。

日期以年/月/日  来建，当然也可以  年-月/日/， 或者年-月-日/

参考我的  https://github.com/drunkpig/drunkpig.github.io/tree/source

然后在工程目录下建立一个.travis.yml文件，内容如下，直接copy:



```yaml
language: python
dist: bionic
sudo: required

python:
    - "3.7"

branches:
  only:
    - source
    - master

install:
  - pip install -U git+https://github.com/drunkpig/mdwiki.git
  - sudo snap install tree

script:
  - mdpub
```



#### 步骤2. 授权travis-ci

去https://travis-ci.com/ ， 把你的这个博客仓库授权给他构建。



#### 步骤3. 在travis-ci上配置几个变量

进入你授权的仓库的setting里，配置几个环境变量

![](docs\配置参数.png)



- GITHUB_TK  去你的github  https://github.com/settings/tokens  新建一个
- REPO_URL  你的博客的github地址，注意是https://开头的，不支持git://开头
- U_EMAIL  你的github email
- U_NAME 你的github 的名字, 也可以随便写



#### 写博客提交

最后你就可以在你本地使用可视化的markdown 编辑器写博客了。写好之后push到仓库里。travis-ci自动会对博客进行构建，并提交到你的仓库。

还可以给自己的博客绑定个域名，自己去网上查吧，很多介绍。





## 参考资源

- css https://github.com/wecatch/markdown-css
- 分页 http://www.htmleaf.com/Demo/201707054612.html
- 还有一种提交到git的方法 https://garryshield.github.io/2019/04/08/travis-ci/
- https://www.yukunweb.com/2018/2/static-blog-based-on-flask/  参考学习
- 数学公式解析 https://github.com/sJohnsonStoever/python-markdown-mathjax
- bootcss 文档 https://code.z01.com/v4/layout/grid.html
- https://juejin.im/post/5c0a27ee6fb9a049d05d8b70   mathjax
- https://www.caam.rice.edu/~heinken/latex/symbols.pdf mathjax
- [https://oysz2016.github.io/post/8611e6fb.html#%E5%85%B3%E7%B3%BB%E8%BF%90%E7%AE%97%E7%AC%A6](https://oysz2016.github.io/post/8611e6fb.html#关系运算符)  mathjax
- 
