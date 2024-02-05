
import requests
# from enum import Enum
class ApiClient:
	apiUri = 'https://api.elasticemail.com/v2'
	# apiKey = '280A5E84998C4E1CCC2BDFB550198D89B34C7B2D8BB8629187A4B8EEE5314DDD351BD280B6A818758D916ADACDCE7208'
	apiKey = '1396AAD21849A2764E272B0558BD50CE1C5C0AE76EAC6D0C5E7AEF2D6FBE7B13A269FEB4DB70DDAE5497755275659A40'
	def Request(method, url, data):
		data['apikey'] = ApiClient.apiKey
		if method == 'POST':
			result = requests.post(ApiClient.apiUri + url, data = data)
			print(result.json())
		elif method == 'PUT':
			result = requests.put(ApiClient.apiUri + url, data = data)
		elif method == 'GET':
			attach = ''
			for key in data:
				attach = attach + key + '=' + data[key] + '&' 
			url = url + '?' + attach[:-1]
			result = requests.get(ApiClient.apiUri + url)	
			
		jsonMy = result.json()
		
		if jsonMy['success'] is False:
			return jsonMy['error']
			
		return jsonMy['data']

def Send(subject, EEfrom, fromName, to, bodyHtml, bodyText, isTransactional):
	return ApiClient.Request('POST', '/email/send', {
		'subject': subject,
		'from': EEfrom,
		'fromName': fromName,
		'to': to,
		'bodyHtml': bodyHtml,
		'bodyText': bodyText,
		'isTransactional': isTransactional})
				
print(Send("Your Subject", "pradeepgeddada31@gmail.com", "Your Company Name", "govinduraju3288@gmail.com;geddadavenkatapradeep@gmail.com;mentormentee.cse@sathyabama.ac.in", "<h1>Html Body</h1>", "Text Body", False))

# mentormentee.cse@sathyabama.ac.in





# import requests

# url = "https://waapi.app/api/v1/instances/3470/client/action/send-message"

# payload = {
#     "chatId": "919121040119@c.us",
#     "message": "This is a test message. and I mention @123456789 and @987654321",
#     # "mentions": ["919121040119@c.us","917702963099@c.us"]
# }
# headers = {
#     "accept": "application/json",
#     "content-type": "application/json",
#     "authorization": "Bearer 2JOsgGD0oMXNdjTmQKHIVkjRVj8jPsHEB2qe1E9b3b74add8"
# }

# response = requests.post(url, json=payload, headers=headers)

# print(response.text)


