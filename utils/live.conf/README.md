# What is live.conf

This directory contains example files used for LIVE deployment.

You don't have to use these to do development and they are useful only for system administrators who are looking after the live website.

All configuration files are not LIVE ready, they are examples or templates which MUST be modified before they are used.

# What is here

 * wsgi.conf - An important file that is configured to start the python/django service on a localhost port/socket. It's used to boot the website in conjuntion with nginx.
 * nginx.conf - The nginx server configuration with the latest best configurations for ssl, rewrite rules and error handling.
 * cron.jobs - A list of jobs which the website should perform and how often they should be done.
 * local_settings.py - A very important configuration file which sets up exactly how the deployment works in regards to django functionality. It contains many secret keys, API keys, database connection information and other important configurations which are not universal between development and live. (see template below)

# What is not here

 * inkscape/local_settings.py.template - This is the development version of the above local_settings.py and contains values suitable for localhost development and test runner uses. It's automatically installed to inkscape/local_settings.py when django is run and should only be changed rarely.

# Keep it up to date

ALL these files should be kept up to date with the live versions or dev versions, without making them exactly the same. This is important because many settings contain preivate keys and other sensitive information which shouldn't be stored in the website repository.

To keep them up to date, you can copy the new parts into the existing files making them the same, or you can copy the live file over this file. BUT you MUST ALWAYS sanitise the files makign sure to remove all specific information regarding live deployment and replacing it with stand-in information that explains what it is that's missing.

