#!/usr/bin/env bash

cd ..
rm -rf drunkpig.github.io

git clone https://github.com/drunkpig/drunkpig.github.io.git
cd drunkpig.github.io

git config user.name "${U_NAME}"
git config user.email "${U_EMAIL}"

git checkout source
python mdwiki.py  ./post   ../html

git checkout master

branch=$(git symbolic-ref --short -q HEAD)
echo "检测到的branch是${branch}"
if [[ ${branch} == 'master' ]]
then
    echo "分支位于master，开始更新博客内容"
    rm -rf *
	git add .
	git commit -m"delete old"
	
    mv ../html/*  .
    rmdir ../html
	
	echo "准备提交的编译结果如下："
	tree

	# 更新build 时间
	#sed -i "/<\/body>/i  build: `date '+%Y-%m-%d %H:%M:%S'`" index.html
	sed -i "s/__BUILD_VERSION__/`date '+%Y-%m-%d %H:%M:%S'`/"  `grep __BUILD_VERSION__ -rl ./`
	git add .
	git commit -m "Update blog"
	git push -f "https://${GITHUB_TK}@github.com/drunkpig/drunkpig.github.io.git" master
else
    echo "分支切换不成功，更新失败"
	exit 1
fi
