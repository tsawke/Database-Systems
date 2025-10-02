package com.example;
public interface DataManipulation {

    public int addOneMovie(String str);
    public String allContinentNames();
    public String continentsWithCountryCount();
    public String FullInformationOfMoviesRuntime(int min, int max);
    public String findMovieById(int id);
    public String findMoviesByTitleLimited10(String title);
}
