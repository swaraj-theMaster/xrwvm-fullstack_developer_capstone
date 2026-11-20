/*jshint esversion: 8 */
const express = require('express');
const mongoose = require('mongoose');
const fs = require('fs');
const cors = require('cors');
const app = express();
const port = 3030;

app.use(cors());
app.use(require('body-parser').urlencoded({ extended: false }));
app.use(express.json());

const reviews_data = JSON.parse(fs.readFileSync("data/reviews.json", 'utf8'));
const dealerships_data = JSON.parse(fs.readFileSync("data/dealerships.json", 'utf8'));

const mongoUri = process.env.MONGO_URI || "mongodb://mongo_db:27017/";

mongoose.connect(mongoUri, { 'dbName': 'dealershipsDB' })
  .then(() => {
    console.log("Connected to MongoDB successfully");
    Reviews.deleteMany({}).then(() => {
      Reviews.insertMany(reviews_data['reviews']);
    });
    Dealerships.deleteMany({}).then(() => {
      Dealerships.insertMany(dealerships_data['dealerships']);
    });
  })
  .catch((err) => {
    console.log("MongoDB connection error or standalone mode:", err.message);
  });

const Reviews = require('./review');
const Dealerships = require('./dealership');

// Express route to home
app.get('/', async (req, res) => {
  res.send("Welcome to the Mongoose API");
});

// Express route to fetch all reviews
app.get('/fetchReviews', async (req, res) => {
  try {
    if (mongoose.connection.readyState === 1) {
      const documents = await Reviews.find();
      return res.json(documents);
    }
    return res.json(reviews_data['reviews']);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching documents' });
  }
});

// Express route to fetch reviews by a particular dealer
app.get('/fetchReviews/dealer/:id', async (req, res) => {
  try {
    const dealerId = parseInt(req.params.id);
    if (mongoose.connection.readyState === 1) {
      const documents = await Reviews.find({ dealership: req.params.id });
      return res.json(documents);
    }
    const filtered = reviews_data['reviews'].filter(r => r.dealership === dealerId || r.dealership == req.params.id);
    return res.json(filtered);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching documents' });
  }
});

// Express route to fetch all dealerships
app.get('/fetchDealers', async (req, res) => {
  try {
    if (mongoose.connection.readyState === 1) {
      const documents = await Dealerships.find();
      return res.json(documents);
    }
    return res.json(dealerships_data['dealerships']);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching dealerships' });
  }
});

// Express route to fetch Dealers by a particular state
app.get('/fetchDealers/:state', async (req, res) => {
  try {
    const stateParam = req.params.state;
    if (mongoose.connection.readyState === 1) {
      const documents = await Dealerships.find({ state: new RegExp('^' + stateParam + '$', 'i') });
      return res.json(documents);
    }
    const filtered = dealerships_data['dealerships'].filter(
      d => d.state.toLowerCase() === stateParam.toLowerCase()
    );
    return res.json(filtered);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching dealerships by state' });
  }
});

// Express route to fetch dealer by a particular id
app.get('/fetchDealer/:id', async (req, res) => {
  try {
    const dealerId = parseInt(req.params.id);
    if (mongoose.connection.readyState === 1) {
      const document = await Dealerships.findOne({ id: dealerId });
      return res.json(document);
    }
    const dealer = dealerships_data['dealerships'].find(
      d => d.id === dealerId || d.id == req.params.id
    );
    return res.json(dealer || {});
  } catch (error) {
    res.status(500).json({ error: 'Error fetching dealer by id' });
  }
});

// Express route to insert review
app.post('/insert_review', express.raw({ type: '*/*' }), async (req, res) => {
  try {
    let data;
    if (typeof req.body === 'string') {
      data = JSON.parse(req.body);
    } else if (Buffer.isBuffer(req.body)) {
      data = JSON.parse(req.body.toString('utf8'));
    } else {
      data = req.body;
    }

    if (mongoose.connection.readyState === 1) {
      const documents = await Reviews.find().sort({ id: -1 });
      let new_id = (documents.length > 0 && documents[0]['id']) ? documents[0]['id'] + 1 : 1;
      const review = new Reviews({
        "id": new_id,
        "name": data['name'],
        "dealership": data['dealership'],
        "review": data['review'],
        "purchase": data['purchase'],
        "purchase_date": data['purchase_date'],
        "car_make": data['car_make'],
        "car_model": data['car_model'],
        "car_year": data['car_year'],
      });
      const savedReview = await review.save();
      return res.json(savedReview);
    } else {
      let maxId = reviews_data['reviews'].reduce((max, r) => r.id > max ? r.id : max, 0);
      const newReview = {
        id: maxId + 1,
        name: data['name'],
        dealership: parseInt(data['dealership']),
        review: data['review'],
        purchase: data['purchase'],
        purchase_date: data['purchase_date'],
        car_make: data['car_make'],
        car_model: data['car_model'],
        car_year: data['car_year']
      };
      reviews_data['reviews'].push(newReview);
      return res.json(newReview);
    }
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Error inserting review' });
  }
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
