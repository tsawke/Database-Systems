package com.example;

public class Client {

    public static void main(String[] args) {
        try {
            DataManipulation dm = new DataFactory().createDataManipulation("database");
            // dm.addOneMovie("流浪地球;cn;2019;127");
            System.out.println(dm.allContinentNames());
            System.out.println(dm.continentsWithCountryCount());
            //System.out.println(dm.findMovieById(10));

            System.out.println(dm.findMoviesByTitleLimited10("'aba'"));

            System.out.println(dm.findMoviesByTitleLimited10("'aba';drop table movies;--"));
        
            System.out.println(dm.findMoviesByTitleLimited10("aba"));

        } catch (IllegalArgumentException e) {
            System.err.println(e.getMessage());
        }
    }
}

