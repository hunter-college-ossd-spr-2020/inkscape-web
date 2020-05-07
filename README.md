These instructions are subject to change, please email doctormo@gmail.com if
you are having issues getting a local instance working.

Getting the Website Code
========================

 Option A:
    $ git clone https://gitlab.com/inkscape/inkscape-web.git
 Option B (better):
    Create an ssh key if you don't have one yet, and upload your public ssh key to gitlab
    (instructions: https://docs.gitlab.com/ee/gitlab-basics/create-your-ssh-keys.html), then:
    $ git clone git@gitlab.com:inkscape/inkscape-web.git

Running the website locally for Ubuntu Operating System:

 1) $ pip install -r requirements (if you are using python3(3.7+), you can use pip3 instead of pip)
 2) $ ./utils/init
 3) $ ./utils/manage makemigrations
 4) $ ./utils/manage migrate
 5) $ ./utils/manage runserver
 6) Open http://localhost:8000/ in your web browser (recommendation: Firefox or Chrome)
 7) Log in with username "admin" and password "123456"

Updating the Website Code:

 1) git pull
 2) ./utils/update

Updating the CMS Content:

 1) ./utils/refresh-cms

Regenerating the virtual environment (may be needed after system upgrade
or if you change the path name):

 1) rm -rf pythonenv
 2) ./utils/init