#include <time.h>
#include <ctime>
#include <sstream>

// function to parse a date or time string.
time_t parseDateTime(const char* datetimeString, const char* format)
{
    struct tm tmStruct;
    tmStruct.tm_sec = 0;  // in case no sec input
    tmStruct.tm_min = 0;  // in case no min input
    tmStruct.tm_hour = 0;  // in case no hour input
    strptime(datetimeString, format, &tmStruct);
    /*
    cout << datetimeString << endl; 
    cout << "tmStruct y/m/d: " << tmStruct.tm_year+1900 << "/" << tmStruct.tm_mon+1 << "/" << tmStruct.tm_mday
         << "  H:M:S "  << tmStruct.tm_hour << ":" << tmStruct.tm_min << ":" << tmStruct.tm_sec << endl;
    */
    return mktime(&tmStruct);
}
// Function to format a time_t value into a date or time string.
string DateTime(time_t time, const char* format)
{
    char buffer[90];
    struct tm* timeinfo = localtime(&time);
    strftime(buffer, sizeof(buffer), format, timeinfo);
    return buffer;
}
//
// GBCR QC/SEU error injection counter summary 
// input result_dir = sub directory name of a run under QAResults/ 
//
void plotSEU(const string result_dir) {

  string dumpFile = "QAResults/" + result_dir + "/ChAll.TXT";
  ifstream inFile(dumpFile.c_str());
  string line(200,' ');
  if(!inFile.is_open()) { 
    cout << "Error in opening result file: " << dumpFile << endl;
    return;
  } else {
    cout << "Opened dump file: " << dumpFile << endl;    
  }
  //
  // DAQ channel numbers for RXout ports 
  const int maxRX = 7; 
  const int RXout[maxRX]   = { 4, 5, 6,  7,  0, 1, 2 } ;
  //
  // RX/TX channels for DAQ CH*.TXT files: TXn is represented as 10+n  
  const int maxDAQ = 9; 
  const int RXchan[maxDAQ] = { 5, 6, 7, 12,  1, 2, 3, 4, 11 };

  time_t startTime[maxDAQ];
  time_t endTime[maxDAQ];
  int   chanEvent[maxDAQ];
  for(int i=0; i<maxDAQ; i++) { chanEvent[i] = 0;}
  int startGen[maxDAQ], endGen[maxDAQ];
  int startObs[maxDAQ], endObs[maxDAQ];
  
   TH2F* h_errcnt  = new TH2F("herrcnt","Err bit count",33,0.,33.,9,0.,9.);
   TH2F* h_errmask = new TH2F("herrmask","Err bit mask by channel",32,0.,32.,9,0.,9.);
  
  int numline  = 0;
  int indFrame = 0;
  bool DBG = 1;
  const int maxFrame = 2000; 
  
  // Loop over config file lines
  while (! inFile.eof() )
  {
    getline (inFile,line);
    numline++;
    if(DBG) cout << line << endl; 
    //
    // Parse lines into parameters
    //
    if(line!=""){
      
      std::string ch_date_time = line.substr(0,26);
      
      std::string ch_counters  = line.substr(27,line.length());
      int chan, injgen, injobs, delCRC, timeStamp, expCode, obsCode, ErrMask, CDC32;  
      sscanf(ch_counters.c_str(),"%i %i %i %i %i %x %x %x %i",&chan, &injgen, &injobs, &delCRC, &timeStamp, &expCode, &obsCode, &ErrM
ask, &CDC32);

      //printf("%s ch=%i inj gen/obs=%i/%i Code exp/obs/errmask=%08x/%08x/%08x\n", ch_date_time.c_str(), chan, injgen,injobs, expCode, obsCode, ErrMask);  

      int errcnt = 0; 
      for(int m=0;m<32;m++) {
	if((ErrMask&(1<<m))!=0) {
	  errcnt++;
	  h_errmask->Fill(float(m),float(chan),1.0);
	}
      }
      h_errcnt->Fill(float(errcnt),float(chan),1.0);
      //
      //  First entry of a channel
      //
      if(chanEvent[chan]==0) {
	startTime[chan] = parseDateTime(ch_date_time.c_str(),"%F %T");
	startGen[chan] = injgen;
	startObs[chan] = injobs;
      }
      endTime[chan] = parseDateTime(ch_date_time.c_str(),"%F %T");
      endGen[chan] = injgen;
      endObs[chan] = injobs;
      chanEvent[chan]++; 
    }
  }
  cout << "end of file with " << numline << " lines " << endl;
  cout << "End Run Summary" << endl;
  printf("DAQ  Lane Nevt  Date time     Start/ End      dT(min)  Start    Inj/Obs   End      Inj/Obs    Ninj/   Nobs\n");
  for(int j=0;j<maxDAQ;j++) {
    char ch_chan[4];
    if(RXchan[j]<10) { snprintf(ch_chan,4,"RX%i",RXchan[j]); }
    else { snprintf(ch_chan,4,"TX%i",RXchan[j]-10); }
    if(chanEvent[j]==0) { 
      printf("Ch%i %4s %5i\n", j, ch_chan, chanEvent[j]);
    } else {
      string tstart = DateTime(startTime[j]," %F %T");
      string tend   = DateTime(endTime[j],"%T ");
      float delMinute = difftime(endTime[j], startTime[j])/60.;  
      printf("Ch%i %4s %5i %17s/ %9s %6.1f %6i/%10i  %6i/%10i  %6i/%7i\n", j, ch_chan, chanEvent[j],tstart.c_str(),tend.c_str(),delMi
nute,
   	   startGen[j],startObs[j],endGen[j],endObs[j],endGen[j]-startGen[j],endObs[j]-startObs[j]);
    }
  }
      
}
