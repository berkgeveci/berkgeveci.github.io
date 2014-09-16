require 'fileutils'

    task :publish do
      index = '/tmp/blog-index'
      FileUtils.rm_rf(index)
      ENV['GIT_INDEX_FILE'] = index
      sh "jekyll build --lsi"
      sh "cd _site && GIT_DIR=../.git git add ."
      tsha = `git write-tree`.chomp
      msha = `git rev-parse master`.chomp
      csha = `echo 'updated' | git commit-tree #{tsha} -p #{msha}`.chomp
      sh "git update-ref refs/heads/master #{csha}"
      sh "git push -f origin master"
    end
