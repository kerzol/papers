### Stupid, but extensible spam detector

STOP_SPAM_WORDS = ["Loan", "Lender"]

def is_spam(request):
  if 'username' in request.form:
    if any(
        [ word.upper() in request.form['username'].upper()
         for word in STOP_SPAM_WORDS]):
      return True
  return False
