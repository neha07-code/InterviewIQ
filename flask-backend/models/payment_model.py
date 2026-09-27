import mongoose from "mongoose"
import razorpay from "../services/razorpay.service.js"

const paymentSchema = new mongoose.Schema({
    userId:{
        type:mongoose.Schema.Types.ObjectId,
        ref:"user",
        required: true,
    },
    planId:String,
    amount:Number,
    credits: Number,
    razorpayOrderId: String,
    razorpayPaymentId: String,
    status:{
        type:String,
        enum: ["created","paid","failed"],
        default:"created",
    },
},{timestamps:true})

const Payment = mongoose.model("Payment",paymentSchema)

export default Payment