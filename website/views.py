#will have all the routes for pages that does not have authorization#

from flask import Blueprint,render_template,request,redirect,url_for,jsonify
from datetime import datetime
from . import db
from .models import CustomerTicketInformation,sendEmail,User, Message, InternalMessage
from .models import statusEnum,priorityOrder
from flask_login import login_required

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home():
    return render_template("landing.html")

@views.route("/dashboard",methods=['GET'])
def dashboard():
    return render_template("dashboard.html")

@views.route('/submitted',methods=['GET','POST'])
def submitted():
    return render_template("submitted.html")


@views.route('/createTicket',methods=['GET','POST'])
def createTicket():
    if request.method == "POST":
        subject = request.form.get('subject')
        customerFirstName = request.form.get('customer_first_name')
        customerLastName = request.form.get('customer_last_name')
        customerEmail = request.form.get('customer_email')
        businessName = request.form.get('business_name')
        customerNumber = request.form.get('customer_phone')
        problemDescription = request.form.get('description')

        customerInfo = CustomerTicketInformation(subject=subject,firstName=customerFirstName,lastName=customerLastName,
                                                 email=customerEmail,businessName=businessName,phoneNumber=customerNumber,
                                                 description=problemDescription)
        db.session.add(customerInfo)
        db.session.commit()
        now = datetime.now()
        date_time = now.strftime("%m/%d/%Y")
        emailToCustomer = sendEmail(businessName,date_time,reciever_email=customerEmail,subject=subject,ticketId=customerInfo.id)
        emailToCustomer.tickets_recieved_email()
        return redirect(url_for('views.submitted'))
    return render_template("createTicket.html")

@views.route("/getAllTickets")
def getAllTickets():
    ticketDetails = CustomerTicketInformation.query.all()
    tickets = [{'id': ticket.id , 'subject':ticket.subject,'name':ticket.firstName, 'email':ticket.email,"phoneNumber":ticket.phoneNumber,
                "businessName":ticket.businessName,'date':ticket.date,"status":ticket.status.value,"priority":ticket.priority.value,
                'description':ticket.description} for ticket in ticketDetails]
    return jsonify(tickets)
    #route that will pass all tickets that are in database -- so that front end people can use that in javascript

@views.route("/getAllEmployees")
def getAllEmployees():
    workers = User.query.all()
    companyWorkers = [{'id':worker.id,"name":worker.name,"username":worker.username,"role":worker.role} for worker in workers]
    return jsonify(companyWorkers)






@views.route("/deleteUser/<int:employee_id>", methods=['DELETE'])
def deleteUser(employee_id):
    user = User.query.filter_by(id=employee_id).first()

    if user is not None:
        db.session.delete(user)  # Mark the user for deletion
        db.session.commit()  # Commit the transaction
        return jsonify({"message": "User deleted successfully"})
    else:
        return jsonify({"error": "User not found"}, 404)


#route created for resolveTicket
@views.route("/resolveTicket/<int:ticket_id>",methods=['POST'])
def resolveTicket(ticket_id):
    ticket = CustomerTicketInformation.query.get(ticket_id)
    if ticket is None:
        return "Ticket not found", 404
    ticket.status = statusEnum.RESOLVED
    ticket.priority = priorityOrder.NONE
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y")
    emailToCustomer = sendEmail(ticket.businessName,date_time,reciever_email=ticket.email,subject=ticket.subject,ticketId=ticket.id)
    emailToCustomer.statusChange()
    db.session.commit()
    return "Ticket resolved successfully"

#added routes for unresolve Ticket
@views.route("/unresolveTicket/<int:ticket_id>",methods=['POST'])
def unresolveTicket(ticket_id):
    ticket = CustomerTicketInformation.query.get(ticket_id)
    if ticket is None:
        return "Ticket not found", 404
    ticket.status = statusEnum.UNRESOLVED
    db.session.commit()
    return "Ticket resolved successfully"

#added routes for highPriority Ticket
@views.route("/highPriorityTicket/<int:ticket_id>",methods=['POST'])
def highPriorityTicket(ticket_id):
    ticket = CustomerTicketInformation.query.get(ticket_id)
    if ticket is None:
        return "Ticket not found", 404
    ticket.priority = priorityOrder.HIGHPRIORITY
    db.session.commit()
    return "Ticket resolved successfully"

#added routes for lowPriority Ticket
@views.route("/lowPriorityTicket/<int:ticket_id>",methods=['POST'])
def lowPriorityTicket(ticket_id):
    ticket = CustomerTicketInformation.query.get(ticket_id)
    if ticket is None:
        return "Ticket not found", 404
    ticket.priority = priorityOrder.LOWPRIORITY
    db.session.commit()
    return "Ticket resolved successfully"

# #completed the changing the status and the priority of the tickets

# @views.route('/customerComment/<int:ticket_id>',methods=['GET'])
# def customerComments(ticket_id):
#     ticket = CustomerTicketInformation.query.get(ticket_id)
#     if ticket is None:
#         return "Ticket not found",404
#     return jsonify(ticket)


######Ticket Commenting####

@views.route("/customerComments",methods=['GET'])
def customerComments():
    return render_template("customerComments.html")

@views.route("/adminComments",methods=['GET'])
def adminComments():
    return render_template('adminComments.html')


# this will return the ticket the main chat messages -- for a particular ticketId
@views.route("/<int:ticket_id>/getMessages")
def getTicketMessagesById(ticket_id):
    ticket = db.session.query(CustomerTicketInformation).filter(CustomerTicketInformation.id == ticket_id).first()
    if ticket:
        # Access the ARRAY of JSON strings
        messages = [{"text": message.text, "sender": message.sender, "timestamp": message.timestamp} for message in ticket.messages]
        return jsonify(messages)
    else:
        return []


#This will get the internal messages for a ticket --> the internal messages are not seen by customers only team members can see those messages
@views.route("/<int:ticket_id>/getInternalMessages")
def getInternalMessagesById(ticket_id):
    ticket = db.session.query(CustomerTicketInformation).filter(CustomerTicketInformation.id == ticket_id).first()
    if ticket:
        messages = [{"text": message.text, "sender": message.sender, "timestamp": message.timestamp} for message in ticket.internalMessages]
        return jsonify(messages)
    else:
        return []


#this will get the ticket by their id's
@views.route("/<int:ticket_id>")
def getTicketById(ticket_id):
    ticket = db.session.query(CustomerTicketInformation).filter(CustomerTicketInformation.id == ticket_id).first()
    if ticket is not None:
        ticket_info = {
            'id': ticket.id,
            'subject': ticket.subject,
            'name': ticket.firstName +" "+ ticket.lastName,
            'email': ticket.email,
            'phoneNumber': ticket.phoneNumber,
            'businessName': ticket.businessName,
            'date': ticket.date,
            'status': ticket.status.value,
            'priority': ticket.priority.value,
            'description': ticket.description
        }
        return jsonify(ticket_info)
    else:
        return "Ticket not found", 404


#Post request called when a new main massage is to be submitted to database
@views.route('/submitNewMessage', methods=['POST'])
def submitMessage():
    if request.method == "POST":
        
        message = request.get_json()

        messageText = message.get("text")
        currentSender = message.get("sender")
        currentTime = message.get("timestamp")
        ticketNum = message.get("ticketNum")

        ticket = db.session.query(CustomerTicketInformation).filter(CustomerTicketInformation.id == ticketNum).first()
        if ticket:
            # Create a new message object
            new_message = Message(text=messageText, sender=currentSender, timestamp=currentTime)
            new_message.ticket = ticket
            ticket.messages.append(new_message)

            db.session.commit()

            # Check if the custom header 'X-Page' is present and has the value 'adminComments'
            if request.headers.get('X-Page') == 'adminComments':
                # The request was sent from the "adminComments.html" page #send email update
                emailToCustomer = sendEmail(ticket.businessName,ticket.date,ticket.email,ticket.subject,ticket.id)
                emailToCustomer.adminAddedNewMessage_email()

            return jsonify({"message": "Message added successfully"})
        else:
            return jsonify({"message": "Not a valid ticket number"})

    return jsonify({"message": "Invalid request"})




#this will store the internal comments that customer cannot see, only team members can see those messages
@views.route('/submitNewInternalMessage', methods=['POST'])
def submitInternalMessage():
    if request.method == "POST":
        message = request.get_json()

        messageText = message.get("text")
        currentSender = message.get("sender")
        currentTime = message.get("timestamp")
        ticketNum = message.get("ticketNum")

        ticket = db.session.query(CustomerTicketInformation).filter(CustomerTicketInformation.id == ticketNum).first()

        if ticket:
            # Create a new message object
            new_message = InternalMessage(text=messageText, sender=currentSender, timestamp=currentTime)
            new_message.ticket = ticket
            ticket.internalMessages.append(new_message)

            db.session.commit()

            return jsonify({"message": "Message added successfully"})
        else:
            return jsonify({"message": "Not a valid ticket number"})

    return jsonify({"message": "Invalid request"})
