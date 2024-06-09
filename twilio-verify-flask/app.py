import ldclient, os, validators
from flask import Flask, request, render_template
from ldclient import Context
from ldclient.config import Config
from twilio.rest import Client


twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_verify_services_sid = os.getenv("TWILIO_VERIFY_SERVICES_SID")

app = Flask(__name__)

# instantiate Twilio client helper library
client = Client(twilio_account_sid, twilio_auth_token)

ld_sdk_key = os.getenv("LAUNCHDARKLY_SDK_KEY")
feature_flag_key = os.getenv("LAUNCHDARKLY_FLAG_KEY")
ldclient.set_config(Config(ld_sdk_key))


@app.route("/")
def registration_page():
    return render_template('register.html')


@app.route("/register", methods=('POST',))
def register():
    email = request.form['email']
    phone_number = request.form['phone']
    password = request.form['password']
    verify_code = request.form.get('verify_code', '')
    if not validators.email(email):
        return "<h1>You need to specify a valid 'email'.</h1>"
    # specify the user and email to LaunchDarkly as a Context 
    context = Context.builder('twilio-verify-app').kind('user')\
                                                  .set("email", email).build()

    # if verify token, check it for validity
    if verify_code:
        check_verify_token = verification_check = client.verify.v2 \
                               .services(twilio_verify_services_sid) \
                               .verification_checks \
                               .create(to=phone_number, code=verify_code)
    # LaunchDarkly evaluates whether additional verification is required
    flag_verify = ldclient.get().variation(feature_flag_key, context, False)
    if verify_code and check_verify_token.status == "approved":
        return "<h1>Verification successful! Registration complete.</h1>"
    elif flag_verify:
        verification = client.verify.v2.services(twilio_verify_services_sid) \
                       .verifications.create(to=phone_number, channel='sms')
        return render_template('verify.html')
    else:
        # no additional verification required
        # this is where you'd save registration to database
        return "<h1>Registration successful!</h1>"
