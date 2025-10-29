
"use client"
import React from 'react'
import Navbar from "@/app/components/Navbar"
import Hero from "@/app/components/Hero"
import Companies from "@/app/components/companies"
import Footer from "@/app/components/Footer"

const page = () => {
  return (
  <>
    <Navbar />
    <Hero />
    <Companies/>
    <Footer />
  </>
  )
}

export default page