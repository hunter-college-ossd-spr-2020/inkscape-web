These instructions are subject to change, please email doctormo@gmail.com if
you are having issues getting a local instance working.

Getting the Website Code
========================

 Option A:
 ```sh
    $ git clone https://gitlab.com/inkscape/inkscape-web.git
 ```

 Option B (better):
    Create an ssh key if you don't have one yet, and upload your public ssh key to gitlab
    <br>
    (instructions: https://docs.gitlab.com/ee/gitlab-basics/create-your-ssh-keys.html), then:
 ```sh
    $ git clone git@gitlab.com:inkscape/inkscape-web.git
 ```
Running the website locally for Ubuntu Operating System:
```sh
  $ pip install -r requirements (if you are using python3(3.7+), you can use pip3 instead of pip)
  $ ./utils/init
  $ ./utils/manage makemigrations
  $ ./utils/manage migrate) $ ./utils/manage runserver

  Open http://localhost:8000/ in your web browser (recommendation: Firefox or Chrome)
  Log in with username "admin" and password "123456"
```


Updating the Website Code:
```sh
   $ git pull
   $ ./utils/update
```

Updating the CMS Content:
```sh
   $ ./utils/refresh-cms
```
Regenerating the virtual environment (may be needed after system upgrade
or if you change the path name):
```sh
   $ rm -rf pythonenv
   $ ./utils/init
```

You can visit the inkscape website wiki by clicking the following [link](https://wiki.inkscape.org/wiki/index.php/WebSite)