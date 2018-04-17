from papersite import app
from flask import render_template

### About
###############################
                  ##################
            ############
@app.route("/about")
def about():
    return render_template('about.html')


### F.A.Q.
###############################
                  ##################
            ############
@app.route("/faq")
def faq():
    return render_template('faq.html')


### Partners & Donors
###############################
                  ##################
            ############
@app.route("/partners-and-donors")
def partners():
    return render_template('partners.html')


@app.route('/stranger', methods=['GET'])
def stranger():
    return render_template('users/stranger.html')

@app.errorhandler(404)
def page_not_found(e):
    return '<h1>Requested URL is not found, but please \
                take this Kolbenluftpumpe:</h1>        \
            <center>                                   \
                <img src="/static/img/717px-Kolbenluftpumpe_hg.jpg">\
            </center>', 404
