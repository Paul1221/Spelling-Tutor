const express = require('express')
const path = require('path');
const app = express()
const port = 3000

app.use(express.static(__dirname + '/public'));

app.get('/pronunciation', (req, res) => {
  res.sendFile(path.join(__dirname, '/pronunciation.html'))
})

app.get('/login', (req, res) => {
    res.sendFile(path.join(__dirname, '/login.html'))
})

app.get('/home', (req, res) => {
    res.sendFile(path.join(__dirname, '/index.html'))
})

app.get('/register', (req, res) => {
    res.sendFile(path.join(__dirname, '/register.html'))
})

app.get('/grammar', (req, res) => {
    res.sendFile(path.join(__dirname, '/grammarcheck.html'))
})

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
})