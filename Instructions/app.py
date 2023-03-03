import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import datetime as dt
from dateutil.relativedelta import relativedelta



# Database Setup
engine = create_engine("sqlite:///./Resources/hawaii.sqlite")

# Reflect an existing database into a new model.
Base = automap_base()
# Reflect the tables.
Base.prepare(engine, reflect=True)

# Save reference to the tables.
Measurement = Base.classes.measurement
Station = Base.classes.station
# print(Base.classes.keys())


# Flask Setup
app = Flask(__name__,static_url_path='/Images/Honolulu_image')


# Flask Routes
# Set the home page,and List all routes that are available. For easy to use I hyperlink the list
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"<h1>Climate App API</h1>"
        f"Flask API for Climate Analysis.<br/><br/><br/>"
        f"<img width='700' src='https://i0.wp.com/onedayitinerary.com/wp-content/uploads/2020/02/One-day-in-Honolulu-Itinerary.jpg?fit=800%2C600&ssl=1'/ >"

        f"<h2>Available Routes:</h2></br>"
            
            f'<a href="http://127.0.0.1:5000/api/v1.0/precipitation" target="_blank">'
                f"<ol><li>/api/v1.0/precipitation</a></li><br/></br>"
            f'<a href="http://127.0.0.1:5000/api/v1.0/stations" target="_blank">'            
                f"<li>/api/v1.0/stations</a></li><br/><br/>"
            f'<a href="http://127.0.0.1:5000/api/v1.0/tobs" target="_blank">'    
                f"<li>/api/v1.0/tobs</a></li><br/><br/>"
            f'<a href="http://127.0.0.1:5000/api/v1.0/2017-08-23" target="_blank">'
                f"<li>/api/v1.0/start</a></li><br/><br/>"
            f'<a href="http://127.0.0.1:5000/api/v1.0/2016-08-23/2017-08-23" target="_blank">'         
                f"<li>/api/v1.0/start/end</a></li></ol><br/><br/>"     
            )


@app.route("/api/v1.0/precipitation")
def precipitation():
    """Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value"""
    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # Calculate the date 1 year ago from the last data point in the database.
    last_measurement_data_point_tuple = session.query(
        Measurement.date).order_by(Measurement.date.desc()).first()
    (latest_date, ) = last_measurement_data_point_tuple
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - relativedelta(years=1)

    # Perform a query to retrieve the data and precipitation scores.
    data_from_last_year = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= date_year_ago).all()

    session.close()

    # Convert the query results to a dictionary using date as the key and prcp as the value.
    all_precipication = []
    for date, prcp in data_from_last_year:
        if prcp != None:
            precip_dict = {}
            precip_dict[date] = prcp
            all_precipication.append(precip_dict)

    # Return the JSON representation of dictionary.
    return jsonify(all_precipication)


@app.route("/api/v1.0/tobs")
def tobs():
    """Query the dates and temperature observations of the most-active station for the previous year of data."""
    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # Calculate the date 1 year ago from the last data point in the database.
    last_measurement_data_point_tuple = session.query(
        Measurement.date).order_by(Measurement.date.desc()).first()
    (latest_date, ) = last_measurement_data_point_tuple
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - relativedelta(years=1)

    # Find the most active station.
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count().desc()).\
        first()

    # Get the station id of the most active station.
    (most_active_station_id, ) = most_active_station
    print(
        f"The station id of the most active station is {most_active_station_id}.")

    # Perform a query to retrieve the data and temperature scores for the most active station from the last year.
    data_from_last_year = session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station_id).filter(Measurement.date >= date_year_ago).all()

    session.close()

    # Convert the query results to a dictionary using date as the key and temperature as the value.
    all_temperatures = []
    for date, temp in data_from_last_year:
        if temp != None:
            temp_dict = {}
            temp_dict[date] = temp
            all_temperatures.append(temp_dict)
    # Return the JSON representation of dictionary.
    return jsonify(all_temperatures)


@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query for stations.
    stations = session.query(Station.station, Station.name,
                             Station.latitude, Station.longitude, Station.elevation).all()

    session.close()

    # Convert the query results to a dictionary.
    all_stations = []
    for station, name, latitude, longitude, elevation in stations:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        all_stations.append(station_dict)

    # Return the JSON representation of dictionary.
    return jsonify(all_stations)


@app.route('/api/v1.0/<start>', defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
def determine_temps_for_date_range(start, end):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range."""
    """For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date."""
    """For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive."""
    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # If we have both a start date and an end date.
    if end != None:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).filter(
            Measurement.date <= end).all()
    # If we only have a start date.
    else:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()

    session.close()

    # Convert the query results to a list.
    temperature_list = []
    no_temperature_data = False
    for min_temp, avg_temp, max_temp in temperature_data:
        if min_temp == None or avg_temp == None or max_temp == None:
            no_temperature_data = True
        temperature_list.append(min_temp)
        temperature_list.append(avg_temp)
        temperature_list.append(max_temp)
    # Return the JSON representation of dictionary.
    if no_temperature_data == True:
        return f"No temperature data found for the given date range. Try another date range."
    else:
        return jsonify(temperature_list)


if __name__ == '__main__':
    app.run(debug=True)