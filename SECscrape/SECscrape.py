from bs4 import BeautifulSoup
import urllib
from urllib import request
import re
import csv
import os.path
import time
import datetime
import codecs

import http.client

http.client.HTTPConnection._http_vsn = 10
http.client.HTTPConnection._http_vsn_str = 'HTTP/1.0'


def readfromweb(year, quarter):
    data = urllib.request.urlopen(
        "https://www.sec.gov/Archives/edgar/full-index/%s/QTR%s/company.idx" % (year, quarter))
    datastring = data.read()

    return datastring


def readfromfile(year, quarter):
    with open("%s_%s.idx" % (year, quarter), "r") as f:
        return f.read()


def writecsv(l, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(l)


def readindex(year, quarter):
    print(year, quarter)

    if not os.path.exists("%s_%s.idx" % (year, quarter)):
        with open("%s_%s.idx" % (year, quarter), "wb") as f:
            f.write(readfromweb(year, quarter))

    print("readfromweb complete")

    data = readfromfile(year, quarter)

    print("readfromfile complete")

    datalines = data.split("\n")
    print(len(datalines))
    print(datalines[0:10])
    assert re.match("^-+$", datalines[9])
    datakeep = []
    datareject = []
    i = 0
    for line in datalines[10:]:
        companyName = line[0:62].strip()
        formTypes = line[62:74].strip()
        CIK = line[74:86].strip()
        date = line[86:98].strip()
        URL_10k = line[98:].strip()
        if re.search('10[ -]?[kK]', formTypes) and not re.search('NT', formTypes):
            datakeep.append([companyName, formTypes, CIK, date, URL_10k])
        else:
            datareject.append([companyName, formTypes, CIK, date, URL_10k])

        i = i + 1
    ##        if i==100:
    ##            ##print(datakeep)
    ##            break
    writecsv(datakeep, "%s_%s.csv" % (year, quarter))
    writecsv(datareject, "%s_%s_rej.csv" % (year, quarter))


def readforms(year, quarter):
    ##    global alternate_exists
    ##    print(mode)

    with open("%s_%s.csv" % (year, quarter), "r") as URLfile:
        datareader = csv.reader(URLfile)
        name = []
        cik = []
        date = []
        URLs = []
        forms = []
        for row in datareader:
            URLs.append(row[4])
            forms.append(row[1])
            name.append(row[0])
            cik.append(row[2])
            date.append(row[3])
    datamax = 0

    problems = []
    rowtowrite = []
    rowtowrite.append(["CIK",
                       "Name",
                       "Form",
                       "Filing date",
                       "Filing year",
                       "Filing quarter",
                       "URL of form",
                       "public float 1",
                       "public float 2",
                       "extract",
                       "point of public float",
                       "position of something...",
                       "checkbox extract",
                       "LAF", "AF", "NAF", "SRC",
                       "LAF2", "AF2", "NAF2", "SRC2",
                       "Filing status",
                       "FYenddate",
                       "FY year",
                       "Filer status, alternate",
                       "Accelerated filer status, pre-2005",
                       "Filing status 2"])
    parser_set = ["html.parser", "html5lib", "lxml"]
    checkboxtestset = ["whether the registrant is a large accelerated",
                       "whether registrant is a large accelerated",
                       "if the registrant is a large accelerated",
                       "if the company is a large accelerated",
                       "if company is a large accelerated",
                       "if registrant is a large accelerated",
                       "is one of the following: (1) large accelerated",
                       "whether each registrant is a large accelerated",
                       "if each registrant is a large accelerated"]
    accfilchecks = ["the agg",
                    "state",
                    "the appro",
                    " at ",
                    "based",
                    "indicate",
                    " on ",
                    "(1)",
                    "aggregate",
                    " 1 ",
                    "-1-",
                    ".---",
                    "as the reg",
                    "table",
                    "the common",
                    "the registrant",
                    "the number",
                    "the issuer",
                    "explanatory",
                    "-at",
                    "*this",
                    "* this",
                    "the market",
                    "market",
                    "issuer",
                    "registrant does",
                    "non-aff",
                    "for the year",
                    "cover",
                    "form 10",
                    "registrant had",
                    "all of",
                    "part i item",
                    "there is ",
                    "there were",
                    "see page",
                    "this doc",
                    "applicable",
                    "the company",
                    "upon",
                    "-----",
                    "the closing",
                    "number of",
                    "shares of",
                    "wholly",
                    "while",
                    "-on",
                    "no voting",
                    "this annual",
                    "none of",
                    "page",
                    "all outstanding",
                    "all common",
                    "registrant has",
                    "the members",
                    "portions of",
                    "the limited",
                    "because",
                    "[cover",
                    "the [",
                    "common stock",
                    "revenues",
                    "(form",
                    "nbsp"]
    chbxts = ["(check one):",
              "(check one).",
              "(check one)",
              "12b-2).",
              "12b-2.",
              "exchange act.",
              "exchange act:",
              "exchange act).",
              "exchange act):",
              "exhange act)",
              "exchange act .",
              "of the act).",
              "of the act.",
              "or a smaller reporting company.",
              "or a smaller reporting company:",
              "or a non-accelerated filer.",
              "or a non-accelerated filer:",
              "of 1934:",
              "of 1934).",
              "of 1934.",
              "of 1934)",
              "of 1934",
              "of the exchange act",
              "or a smaller reporting company",
              "or a non-accelerated filer",
              "12b-2",
              "12b"]

    ##    print("rowwritten")
    ##    URLs = ["edgar/data/702259/0000950148-03-000640.txt"]

    for i in range(len(URLs)):  ## set to range(1000) when running abbreviated
        ##        if i<5195:
        ##            continue
        largest = "none"
        trymarker = 0
        ##        if quarter == 1:
        ##            continue
        ##        if i<5205:
        ##            continue
        ##        if i>80:
        ##            continue
        ##        print(i)
        filingstatus = ""
        filingstatus2 = ""
        FYenddate = ""
        FY_year = ""
        pointofPF = 0
        FYenddatechecks = [" or ",
                           " |",
                           "-",
                           "transition report",
                           " [",
                           " _",
                           ".",
                           " file",
                           " commission",
                           " restated"]
        mktval = "blank market val"
        largest = "blank largest val"
        bartsection = ""

        LAF2 = ""
        ##        print("inside for loop")
        ##        print(URLs[i])
        try:
            data = urllib.request.urlopen("http://www.sec.gov/Archives/%s" % (URLs[i]), timeout=10).read(100000)
        ##            print(type(data))
        ##        print("URL opened")
        ##souptext = str(data)
        except urllib.error.URLError:
            data = " "
            rowtowrite.append(
                [cik[i], name[i], forms[i], date[i], year, quarter, "http://www.sec.gov/Archives/%s" % (URLs[i]),
                 "timeout error"])
            continue
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            rowtowrite.append(
                [cik[i], name[i], forms[i], date[i], year, quarter, "http://www.sec.gov/Archives/%s" % (URLs[i]),
                 "other URL reading error"])
            continue
        try:
            souptext = data.decode('utf-8')
            ##            tabcon = souptext.find("TABLE OF CONTENTS")
            ##            if tabcon != -1:
            ##                souptext = souptext[0:tabcon+1]
            docref = souptext.find("DOCUMENTS INCORPORATED BY REFERENCE")
            if docref != -1:
                souptext = souptext[0:docref + 1]
            souptextup = souptext.upper()

            p1 = souptext.find("PART I ITEM 1")
            if p1 != -1:
                souptext = souptext[0:p1]
            docref = souptextup.find("DOCUMENTS INCORPORATED BY REFERENCE")
            if docref != -1:
                souptext = souptext[0:docref + 1]
            ##            jpegloc = souptextup.find(".JPG")
            ##            if jpegloc !=-1:
            ##                souptext = souptext[0:jpegloc+1]
            ##            else:
            ####                print(i)
            ####                print("it wasn't found!")
            ##                if len(souptext)>50000:
            ##                    souptext = souptext[0:49999]
            souptextforparse = souptext
            for parsing in parser_set:
                ##                print(parsing)
                try:
                    soup = BeautifulSoup(souptextforparse, parsing)
                    break
                ##            print("souped")
                except RuntimeWarning:
                    print("RUNTIME WARNING EXCEPTION!!!!!!!!!!!!!!!!!")
                    if parsing == "html5lib":
                        souptext = " "
                        soup = " "
                    ##                    print(URLs[i])
                    problems.append([year, quarter, URLs[i], "runtime warning exception"])
                    continue
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except:
                    print("EXCEPTION!!!!!!!!!!!!!!!!!")
                    if parsing == "html5lib":
                        souptext = " "
                        soup = " "
                    ##                    print(URLs[i])
                    problems.append([year, quarter, URLs[i], "parser exception 1"])
                    continue
            ##            print(len(souptext))
            ##            data.close()

            ##            if i==16:
            ##                print(souptext)
            souptext = soup.get_text(" ", strip=True)

            ##            if i==16:
            ##                print(souptext)

            souptext = souptext.replace("\\n", " ")
            souptext = souptext.replace("\n", " ")
            souptext = souptext.replace("Series", " Series")
            souptext = souptext.replace("$ ", "$")
            souptext = souptext.replace("$_", "$0 ")
            souptext = souptext.replace(" ", " ")
            souptext = souptext.replace(".(", ". (")
            souptext = souptext.replace(u'\xa0', u' ')
            souptext = souptext.replace("non &#150;acc", "non-acc")
            souptext = souptext.replace("$-0-", "$0")
            souptext = souptext.replace("nonaffiliates", "non-affiliates")
            souptext = souptext.replace("nonaccelerated", "non-accelerated")
            souptext = souptext.replace("Non accelerated", "Non-accelerated")
            souptext = souptext.replace("Non Accelerated", "Non-accelerated")
            souptext = souptext.replace("non accelerated", "Non-accelerated")
            souptext = souptext.replace("Nonaccelerated", "Non-accelerated")
            souptext = souptext.replace("12(b)-2", "12b-2")
            souptext = souptext.replace("12(b)2", "12b-2")
            souptext = souptext.replace("12-b2", "12b-2")
            souptext = souptext.replace("12-b-2", "12b-2")
            souptext = souptext.replace("filler", "filer")
            souptext = souptext.replace("$USD", "$")
            souptext = souptext.replace("USD", "$")
            souptext = souptext.replace("$US", "$")
            souptext = souptext.replace("$$", "$")
            souptext = souptext.replace("$ ", "$")
            souptext = souptext.replace("&nbsp;", " ")
            souptext = " ".join(souptext.split())

            souptextlower = souptext.lower()
            ##            if i==16:
            ##                print(souptext)

            pointofPF = souptextlower.find("non-affiliates")

            donotcheckfind = souptextlower.find("(do not check", souptextlower.find("accelerated"))
            if donotcheckfind < 0:
                donotcheckfind = souptextlower.find("(do not mark", souptextlower.find("accelerated"))
            donotcheckend = souptextlower.find(")", donotcheckfind)
            if donotcheckfind > 0:
                souptext = souptext.replace(souptext[donotcheckfind:donotcheckend + 1], "")
            souptext = " ".join(souptext.split())

            ##            tabcon = souptext.find("TABLE OF CONTENTS")
            ##            if tabcon != -1:
            ##                souptext = souptext[0:tabcon+1]
            p1 = souptext.find("PART I ITEM 1")
            if p1 != -1:
                souptext = souptext[0:p1]
            docref = souptext.find("DOCUMENTS INCORPORATED BY REFERENCE")
            if docref != -1:
                souptext = souptext[0:docref + 1]
            souptextup = souptext.upper()
            docref = souptextup.find("DOCUMENTS INCORPORATED BY REFERENCE")
            if docref != -1:
                souptext = souptext[0:docref + 1]

            souptext = " ".join(souptext.split())

            ##            print("soup replacements made")

            souptext_noascii = removeNonAscii(souptext)
            souptext_noascii = souptext_noascii.replace("non- aff", "non-aff")
            souptext_noascii = souptext_noascii.replace("non aff", "non-aff")
            souptext_noascii = " ".join(souptext_noascii.split())

            lct = (souptext_noascii.find("held by non-affiliates"))
            ##            if lct != -1:
            ##                break
            if lct == -1:
                lct = souptext_noascii.find("by non-affiliates")
            pos = souptext_noascii.find("$", lct)
            ##            pointofPF = pos
            souptextlower = souptext_noascii.lower()
            souptext2 = souptext
            souptext = souptext_noascii

            ##            if i ==16:
            ##                print(souptext)

            if lct == -1:
                if souptextlower.find("no public market for the registrant’s common stock") > 0:
                    mktval = "no public market"
                elif souptextlower.find("no definition available", lct - 200, lct + 400) > 0:
                    mktval = "no definition available"
                elif souptextlower.find("because the registrant is a wholly-owned subsidiary") > 0:
                    mktval = "wholly owned subsidiary"
                elif souptextlower.find(
                        "none of the registrant's outstanding voting stock is held by non-affiliates") > 0:
                    mktval = "none held by non-affiliates"
                elif souptextlower.find("registrant has no voting common equity") > 0:
                    mktval = "no voting common equity"
                elif souptextlower.find("no established public trading market for registrant’s units") > 0:
                    mktval = "no public trading market"
                elif souptextlower.find("there are no non-affiliate shareholders of the registrant.") > 0:
                    mktval = "no non-affiliates"
                else:
                    mktval = "not given"
            else:
                souptextlower = souptext.lower()
                if pos - lct > 700 or pos == -1:
                    if souptextlower.find("no public market for the registrant’s common stock", lct - 200,
                                          lct + 400) > 0:
                        mktval = "no public market"
                    elif souptextlower.find("no definition available", lct - 200, lct + 400) > 0:
                        mktval = "no definition available"
                    elif souptextlower.find("because the registrant is a wholly-owned subsidiary", lct - 200,
                                            lct + 400) > 0:
                        mktval = "wholly owned subsidiary"
                    elif souptextlower.find(
                            "none of the registrant's outstanding voting stock is held by non-affiliates", lct - 200,
                            lct + 400) > 0:
                        mktval = "none held by non-affiliates"
                    elif souptextlower.find("registrant has no voting common equity", lct - 200, lct + 400) > 0:
                        mktval = "no voting common equity"
                    elif souptextlower.find("no established public trading market for registrant’s units", lct - 200,
                                            lct + 400) > 0:
                        mktval = "no public trading market"
                    elif souptextlower.find("There are no non-affiliate shareholders of the Registrant.", lct - 200,
                                            lct + 400) > 0:
                        mktval = "no non-affiliates"
                    else:
                        mktval = "not given"
                else:
                    if souptextlower.find("no public market for the registrant’s common stock", lct - 200,
                                          lct + 400) > 0:
                        mktval = "no public market"
                    elif souptextlower.find("no definition available", lct - 200, lct + 400) > 0:
                        mktval = "no definition available"
                    elif souptextlower.find("because the registrant is a wholly-owned subsidiary", lct - 200,
                                            lct + 400) > 0:
                        mktval = "wholly owned subsidiary"
                    elif souptextlower.find(
                            "none of the registrant's outstanding voting stock is held by non-affiliates", lct - 200,
                            lct + 400) > 0:
                        mktval = "none held by non-affiliates"
                    elif souptextlower.find("registrant has no voting common equity", lct - 200, lct + 400) > 0:
                        mktval = "no voting common equity"
                    elif souptextlower.find("no established public trading market for registrant’s units", lct - 200,
                                            lct + 400) > 0:
                        mktval = "no public trading market"
                    elif souptextlower.find("There are no non-affiliate shareholders of the Registrant.", lct - 200,
                                            lct + 400) > 0:
                        mktval = "no non-affiliates"
                    basedonstr = souptext[lct:pos]
                    basedon = basedonstr.find("price")
                    if basedon != -1:
                        pos = souptext.find("$", souptext.find("was", basedon + lct))
                        if pos == -1:
                            pos = souptext.find("$", souptext.find(":", basedon + lct))
                    ##                    if i%100==0:
                    ##                        print(souptext[pos:pos+500])
                    spc = souptext.find(" ", pos)
                    ##print(basedonstr)
                    ##print(basedon)
                    ##print(souptext[pos+1:spc])
                    try:
                        mktval = float(
                            souptextlower[pos + 1:spc].replace(",", "").rstrip(".").replace("*", "").replace(";", ""))
                        if mktval < 10000:
                            nxtword = isitmln(souptextlower, pos)
                            if nxtword == "million":
                                mktval = mktval * (10 ** 6)
                            elif nxtword == "billion":
                                mktval = mktval * (10 ** 9)
                            else:
                                newpos = souptextlower.find("$", spc)
                                newspc = souptextlower.find(" ", newpos)
                                ##print(souptext[newpos+1:newspc])
                                try:
                                    mktval = float(
                                        souptextlower[newpos + 1:newspc].replace(",", "").rstrip(".").replace("*",
                                                                                                              "").replace(
                                            ";", ""))
                                    nxtword = isitmln(souptextlower, newpos)
                                    if nxtword == "million":
                                        mktval = mktval * (10 ** 6)
                                    elif nxtword == "billion":
                                        mktval = mktval * (10 ** 9)
                                    else:
                                        mktval = "not given"
                                except ValueError:
                                    mktval = "exception 2"

                    except ValueError:
                        mktval = "error converting to float"
                snippet = souptextlower[lct - 50:lct + 700]
                lrgstval = []
                for match in re.finditer("\$", snippet):
                    pnt = match.start()
                    spce = snippet.find(" ", pnt)
                    try:
                        lrgstvalapp = (
                            float(snippet[pnt + 1:spce].replace(",", "").rstrip(".").replace("*", "").replace(";", "")))
                        nxtword = isitmln(snippet, pnt)
                        if nxtword == "million" and lrgstvalapp < 1000000:
                            lrgstvalapp = lrgstvalapp * (10 ** 6)
                        elif nxtword == "billion" and lrgstvalapp < 1000000000:
                            lrgstvalapp = lrgstvalapp * (10 ** 9)
                        lrgstval.append(lrgstvalapp)
                    except ValueError:
                        pass
                if lrgstval != []:
                    largest = max(lrgstval)
                else:
                    largest = "none"
            souptextlower = souptextlower.replace("for fiscal year", "for the fiscal year")

            if souptextlower.find("for the fiscal year ended") > -1:
                FYenddate = souptextlower[souptextlower.find("for the fiscal year ended") + len(
                    "for the fiscal year ended") + 1:souptextlower.find("for the fiscal year ended") + 150]
                for TRfinder in FYenddatechecks:
                    if FYenddate.find(TRfinder) > -1:
                        FYenddate = FYenddate[0:FYenddate.find(TRfinder)]
                if re.search("[0-9]{4}", FYenddate):
                    matcher = re.search("[0-9]{4}", FYenddate)
                    FY_year = matcher.group()

            if type(lct) is int:
                if lct != -1:
                    extract = souptext[lct:lct + 400]
                else:
                    extract = "none"
            else:
                extract = "none, lct was not integer"

            souptext = souptext2

            souptextlower = souptext.lower()

            souptextendpoint = souptextlower.find("indicate", souptextlower.find("shell") - 200)
            souptext = souptext[0:souptextendpoint]
            souptextlower = souptext.lower()
            strtpt = souptextlower.find("accelerated") - 300
            if strtpt > 0:
                souptextlower = souptextlower[strtpt:]
            endptnew = souptextlower.find("as of", souptextlower.find("accelerated"))
            ## NEED TO DO SOMETHING WITH THE ABOVE LINE
            ## HAD NEEDED TO, NOW IT'S ADDED
            if endptnew != -1:
                souptextlower = souptextlower[:endptnew]
            souptextlower = " ".join(souptextlower.split())

            ## get the check boxes
            checkboxes = 0
            checkboxesmaximin = 0
            checkextract = ""
            LAF = ""
            AF = ""
            NAF = ""
            SRC = ""
            LAF2 = ""
            AF2 = ""
            NAF2 = ""
            SRC2 = ""
            filerstatus_alternate = ""
            accfilerpre2005 = ""
            souptextlower = souptextlower.replace("smaller reporting filer", "smaller reporting company")
            souptextlower = souptextlower.replace("small reporting company", "smaller reporting company")
            souptextlower = souptextlower.replace("non- accelerated", "non-accelerated")
            souptextlower = souptextlower.replace("no n-accelerated", "non-accelerated")
            souptextlower = souptextlower.replace("non accelerated", "non-accelerated")
            souptextlower = souptextlower.replace("nonaccelerated", "non-accelerated")
            souptextlower = souptextlower.replace(" - ", "-")
            souptextlower = souptextlower.replace(" -", "-")
            souptextlower = souptextlower.replace("- ", "-")
            souptextlower = souptextlower.replace("accelerated filed", "accelerated filer")
            souptextlower = souptextlower.replace("accelerate fil", "accelerated fil")
            souptextlower = souptextlower.replace("fil er", "filer")
            souptextlower = souptextlower.replace("larger accelerated", "large accelerated")
            souptextlower = souptextlower.replace("large, accelerated", "large accelerated")
            souptextlower = souptextlower.replace("accelerated file r", "accelerated filer")
            souptextlower = souptextlower.replace("accelerated file ", "accelerated filer ")
            souptextlower = souptextlower.replace("accelerated filter", "accelerated filer")
            donotcheckfind2 = souptextlower.find("(", souptextlower.find("if a smaller") - 50)
            donotcheckend2 = souptextlower.find(")", donotcheckfind2)
            if donotcheckfind2 > 0 and donotcheckend2 > 0:
                souptextlower = souptextlower.replace(souptextlower[donotcheckfind2:donotcheckend2], " ")
            donotcheckfind3 = souptextlower.find("do not check", souptextlower.find("if a smaller") - 50)
            if donotcheckfind3 > 0:
                souptextlower = souptextlower.replace(souptextlower[
                                                      souptextlower.find("do not check"):souptextlower.find(
                                                          "smaller reporting company") + len(
                                                          "smaller reporting company")], "")

            checkone = ""
            checktwo = ""
            if year >= 2002:
                ##                acfilsection = souptextlower.replace("12b-2", "12b-2.")
                ##                acfilsection = acfilsection.replace("exchange act", "exchange act).")
                acfilsection = souptextlower.replace("yes:", "yes;")
                acfilsection = acfilsection.replace("no:", "no;")
                acfilsection = acfilsection.replace("(check mark)", "x")
                acfilsectionpt = acfilsection.find("accelerated filer")
                if acfilsectionpt != -1 and acfilsection.find("large acc") == -1:
                    accfilerpre2005 = acfilsection[acfilsectionpt:acfilsectionpt + 200]
                    if accfilerpre2005.find("yes") != -1:
                        accfilerpre2005 = accfilerpre2005[:accfilerpre2005.find("yes") + 30]
                    for ender in accfilchecks:
                        afep = accfilerpre2005.find(ender)
                        if afep != -1:
                            accfilerpre2005 = accfilerpre2005[:afep].strip()
                    checkone = accfilerpre2005[accfilerpre2005.find("yes"):accfilerpre2005.find("no") + 8]
                    rfinder = accfilerpre2005.rfind(".")
                    while rfinder > accfilerpre2005.find("yes") or rfinder > accfilerpre2005.find(" no"):
                        accfilerpre2005 = accfilerpre2005[:rfinder] + accfilerpre2005[rfinder + 1:]
                        rfinder = accfilerpre2005.rfind(".")
                    bart = min([max([accfilerpre2005.find(")"), accfilerpre2005.find("."), accfilerpre2005.find(":"),
                                     accfilerpre2005.find("the act") + len("the act"),
                                     accfilerpre2005.find("of 1934") + len("of 1934"),
                                     accfilerpre2005.find("exchange act") + len("exchange act"),
                                     accfilerpre2005.find("12b-2") + len("12b-2")]), accfilerpre2005.find("yes") - 3,
                                accfilerpre2005.find("no") - 3])

                    bartsection = accfilerpre2005

                    while bart != -1:
                        bartsection = bartsection[bart + 1:].strip()
                        bart = max([bartsection.find(")"), bartsection.find("."), bartsection.find(":"),
                                    bartsection.find(":")])
                    if "yes" in bartsection:
                        filingstatus2 = filercat(bartsection, 1)
                        filingstatus = filingstatus2

            if year >= 2005:
                for chkbox in checkboxtestset:
                    checkboxesnew = souptextlower.find(chkbox)
                    if checkboxesnew > 0:
                        if checkboxesmaximin == 0:
                            checkboxesmaximin = checkboxesnew
                        else:
                            checkboxesmaximin = min(checkboxesnew, checkboxesmaximin)
                checkboxes = checkboxesmaximin
            if checkboxes > 0:
                checkextract = souptextlower[checkboxes:checkboxes + 1000]
                checkstart = checkextract.find("12b")
                if checkstart < 0:
                    checkstart = checkextract.find(" or ", checkextract.find("accelerated")) + 8
                checkext2 = checkextract[checkstart:]
                sorter = checkextract[checkstart:].replace("ge acc", "")
                sorter = sorter.replace("n-acc", "")

                sorterlister = [["Large accelerated", sorter.find("lareler")],
                                ["Accelerated", sorter.find("accelerated")],
                                ["Non-accelerated", sorter.find("noele")],
                                ["Smaller reporting", sorter.find("smaller")]]
                if checkextract.find("smaller reporting") == -1:
                    sorterlister = sorterlister[0:3]

                ##                second_col = [row[1] for row in sorterlister]
                ##                while -1 in second_col:
                ##                    second_col.remove(-1)
                ##                minseccol = min(second_col)
                checkextract3 = checkextract[:]
                ##                print(i)
                ##                print(name[i])
                ##                print(checkextract3)

                for chkr in chbxts:
                    chkpt = checkextract3.find(chkr)
                    ##                    print(chkr, chkpt)
                    if chkpt != -1:
                        checkextract3 = checkextract3[chkpt + len(chkr):].strip()
                ##                        print(checkextract3)
                ##                        print(chkr)
                ##                        print("just revised")
                ##                print(checkextract3)
                if len(checkextract3) > 2:
                    while (checkextract3[0] == "." or checkextract3[0] == ":" or checkextract3[0] == ")") and len(
                            checkextract3) > 2:
                        checkextract3 = checkextract3[1:].strip()
                ##                        print(checkextract3)

                ##                checkextract = souptextlower[checkboxes:checkboxes+1000]
                ##                print(checkextract)
                ##                print("START")
                ##                print(i)
                ##                print(sorterlister)
                ##                print(checkextract)
                ##                print(checkextract[checkstart:])
                ##                print(checkextract[checkstart+minseccol:])
                ##                filingstatus2 = filercat(checkextract[checkstart+minseccol:], "laf, naf, af, src")
                filingstatus2 = filercat(checkextract3, "laf, naf, af, src")
                ##                print(filingstatus2)
                ##                print(i)
                ##                print("FINISH")
                ## IS the line above correct?
                if sorterlister != sorted(sorterlister, key=lambda position: position[1]):
                    ##                    print("unsorted")
                    problems.append([year, quarter, URLs[i], "sorted incorrectly", sorterlister, checkextract])

                if sorterlister == sorted(sorterlister, key=lambda position: position[1]):
                    if year >= 2008:
                        find1 = checkextract.find("large accelerated filer", checkstart)
                        find2 = checkextract.find("accelerated filer", find1 + 10)
                        find3 = checkextract.find("non-accelerated", find2 + 10)
                        find4 = checkextract.find("smaller reporting", find3)
                        find5 = find4 + len("smaller reporting company") + 10
                        LAF = checkextract[find1:find2]
                        AF = checkextract[find2:find3]
                        NAF = checkextract[find3:find4]
                        if find5 > len(checkextract):
                            SRC = checkextract[find4:]
                        else:
                            SRC = checkextract[find4:find5]
                    elif year >= 2005:
                        find1 = checkextract.find("large accelerated", checkstart)
                        find2 = checkextract.find("accelerated filer", find1 + 10)
                        find3 = checkextract.find("non-accelerated", find2 + 10)
                        find4 = checkextract.find("indicate", find3)
                        LAF = checkextract[find1:find2]
                        AF = checkextract[find2:find3]
                        if find4 > 0:
                            NAF = checkextract[find3:find4]
                        else:
                            NAF = checkextract[find3:]
                elif sorterlister[1][1] > sorterlister[2][1]:
                    ##                    print(sorterlister)
                    ##                    print(URLs[i])
                    if year >= 2008:
                        find1 = checkextract.find("large accelerated filer", checkstart)
                        find2 = checkextract.find("non-accelerated filer", find1 + 10)
                        find3 = checkextract.find("accelerated filer", find2 + 10)
                        find4 = checkextract.find("smaller reporting", find3)
                        find5 = find4 + len("smaller reporting company") + 10
                        LAF = checkextract[find1:find2]
                        NAF = checkextract[find2:find3]
                        AF = checkextract[find3:find4]
                        if find5 > len(checkextract):
                            SRC = checkextract[find4:]
                        else:
                            SRC = checkextract[find4:find5]
                    elif year >= 2005:
                        find1 = checkextract.find("large accelerated", checkstart)
                        find2 = checkextract.find("non-accelerated filer", find1 + 10)
                        find3 = checkextract.find("accelerated", find2 + 10)
                        find4 = checkextract.find("indicate", find3)
                        LAF = checkextract[find1:find2]
                        NAF = checkextract[find2:find3]
                        if find4 > 0:
                            AF = checkextract[find3:find4]
                        else:
                            AF = checkextract[find3:]
                else:
                    ##                    print(sorterlister)
                    ##                    print(URLs[i])
                    ##                    print(sorter)
                    filingstatus = "error in sorting of filing status"
                if year >= 2005:
                    LAF2 = LAF.replace("large accelerated filer", " ")
                    AF2 = AF.replace("accelerated filer", " ")
                    NAF2 = NAF.replace("non-accelerated filer", " ")
                    SRC2 = SRC.replace("smaller reporting company", " ")
                    LAF2 = cleanreturns(LAF2)
                    AF2 = cleanreturns(AF2)
                    NAF2 = cleanreturns(NAF2)
                    SRC2 = cleanreturns(SRC2)
                    ##                LAF2 = LAF2[0:LAF2.find(" ")]
                    ##                AF2 = AF2[0:AF2.find(" ")]
                    ##                NAF2 = NAF2[0:NAF2.find(" ")]
                    ##                SRC2 = SRC2[0:SRC2.find(" ")]

                    if year >= 2008:
                        if LAF2 == AF2 and AF2 == NAF2 and NAF2 != SRC2:
                            filingstatus = "Smaller reporting company"
                        if LAF2 == AF2 and AF2 == SRC2 and AF2 != NAF2:
                            filingstatus = "Non-accelerated filer"
                        if LAF2 == SRC2 and SRC2 == NAF2 and AF2 != SRC2:
                            filingstatus = "Accelerated filer"
                        if LAF2 != AF2 and AF2 == NAF2 and NAF2 == SRC2:
                            filingstatus = "Large accelerated filer"

                    elif year >= 2005:
                        if LAF2 == AF2 and AF2 != NAF2:
                            filingstatus = "Non-accelerated filer"
                        if LAF2 == NAF2 and AF2 != NAF2:
                            filingstatus = "Accelerated filer"
                        if LAF2 != AF2 and AF2 == NAF2:
                            filingstatus = "Large accelerated filer"

            ##            if year >= 2005 and mode== "1":
            ##                if i<60 or alternate_exists > 5:
            ##                    a = time.time()
            ##                    if i%500==0:
            ##                        print("we're in here")
            ####                    print("checking for alternate")
            ##                    try:
            ##                        datafull = urllib.request.urlopen("http://www.sec.gov/Archives/%s" %(URLs[i]), timeout=10).read()
            ##                        datafull = datafull.decode('utf-8')
            ####                        datamax = max(datamax, len(datafull))
            ##                        srchpt = datafull.rfind("entity filer category")
            ##                        dataexcerpt=datafull
            ####                        b = time.time()
            ####                        print("b-a is", b-a)
            ####                        print("length is", len(datafull))
            ##                        if srchpt!=-1:
            ##                            dataexcerpt = datafull[srchpt:srchpt+1000]
            ####                        print(len(dataexcerpt))
            ##                        souptext = "nothing was souped, it was too long"
            ##                        for parsing in parser_set:
            ####                            print(parsing)
            ##                            try:
            ####                                if len(dataexcerpt)<500000:
            ##                                soup = BeautifulSoup(dataexcerpt, parsing)
            ##                                souptext = soup.get_text(" ", strip=True)
            ##
            ##                ##            print("souped")
            ##                            except RuntimeWarning:
            ##                                print("RUNTIME WARNING EXCEPTION")
            ####                                print(URLs[i])
            ##                                problems.append([year, quarter, URLs[i], "runtime warning 2"])
            ##                                continue
            ##                            except KeyboardInterrupt:
            ##                                raise KeyboardInterrupt
            ##
            ##                            except:
            ##                                print("EXCEPTION within alternate check")
            ##                                problems.append([year, quarter, URLs[i], "problem within alternate check"])
            ####                                print(URLs[i])
            ##                                continue
            ##                            break
            ##                        datafull = souptext.lower()
            ##                        searchpoint = datafull.rfind("entity filer category")
            ##                        searchstop = datafull.find("entity", searchpoint + 3)
            ####                        print(searchpoint, i)
            ####                        c = time.time()
            ####                        print("c-b is", c-b)
            ##                        if searchpoint != -1:
            ##                            filerstatus_alternate = datafull[searchpoint:searchstop]
            ##                            alternate_exists+=1
            ####                            if alternate_exists==0:
            ####                                alternate_exists = 1
            ##                    except MemoryError:
            ####                        print("memory error in souping")
            ##                        filerstatus_alternate = "memory error"
            ##                    except KeyboardInterrupt:
            ##                        raise KeyboardInterrupt
            ####                    except:
            ##                        print("Other error in souping")
            ##                        filerstatus_alternate = "other error"
            if i % 500 == 0:
                ##                print(mktval)
                print(i)
                ##                print("alternate exists is", alternate_exists)
                ##                print("datamax is", datamax)
                ##                print("\n \n \n")
                if i % 1000 == 0:
                    print(datetime.datetime.now())
            ##            print(i)
            rowtowrite.append(
                [cik[i], name[i], forms[i], date[i], year, quarter, "http://www.sec.gov/Archives/%s" % (URLs[i]),
                 mktval, largest, extract, pointofPF, checkboxes, checkextract, LAF, AF, NAF, SRC, LAF2, AF2, NAF2,
                 SRC2, filingstatus, FYenddate, FY_year, accfilerpre2005, checkone, bartsection,
                 filingstatus2])  ##, filerstatus_alternate])
        except UnicodeDecodeError:
            rowtowrite.append(
                [cik[i], name[i], forms[i], date[i], year, quarter, "http://www.sec.gov/Archives/%s" % (URLs[i]),
                 "error processing unicode"])
            print("unicode error \n\n\n\n")
        with open("last_10k.txt", "w") as text_file:
            text_file.write("Last 10K was observation %s, CIK %s, name %s, and year %s quarter %s" % (
            i, cik[i], name[i], year, quarter))
    writecsv(rowtowrite, "%s_%s_mktvals.csv" % (year, quarter))
    writecsv(problems, "%s_%s_problems.csv" % (year, quarter))


def isitmln(segment, startpoint):
    nxtword_a = segment.find("$", startpoint)
    nxtword_b = segment.find(" ", nxtword_a)
    mlnword_end = segment.find(" ", nxtword_b + 1)
    mlnword = segment[nxtword_b:mlnword_end].strip().lower().replace(",", "").replace(".", "")
    return mlnword[0:7]


def cleanreturns(stringseg):
    bob = stringseg.replace("_", "")
    bob = bob.replace("[", "")
    bob = bob.replace("]", "")
    bob = bob.replace(" ", "")
    bob = bob.replace("_", "")
    return bob


def filercatlooper(seg, mode=1):
    return None


def filercat(seg, mode=1):
    filestatusmarks = ["x",
                       "Ã",
                       "þ",
                       "ü",
                       "ý"]
    starts = False
    filertyper = []
    file = ""
    if seg.find("[") < seg.find("yes") and seg.find("]") > seg.find("yes"):
        seg = seg.replace("[", "").replace("]", "").strip()
    if seg.find("[") < seg.find("no") and seg.find("]") > seg.find("no"):
        seg = seg.replace("[", "").replace("]", "").strip()
    if mode == 1:
        ##        seg = seg.replace("no", " no")
        breaks = ["yes", "no"]
        breakpts = ["y", "n"]
        sorterlister = [["yes", seg.find("yes"), "yes", "accelerated filer"],
                        ["no", seg.find("no"), "no", "not an accelerated filer"]]
        sortedlist = sorted(sorterlister, key=lambda position: position[1])
    ##        print(seg)
    ##        print(sortedlist)

    else:
        breaks = ["large accelerated filer", "accelerated filer", "non-accelerated filer", "smaller reporting company"]
        ##        print(seg)
        breakpts = ["l", "a", "n", "s"]
        seg = seg.replace("large accelerated filer", "lrg")
        seg = seg.replace("non-accelerated filer", "non")
        seg = seg.replace("accelerated filer", "acf")
        seg = seg.replace("smaller reporting company", "sml")
        sorterlister = [["LAF", seg.find("lrg"), "lrg", "large accelerated filer"],
                        ["AF", seg.find("acf"), "acf", "accelerated filer"],
                        ["NAF", seg.find("non"), "non", "non-accelerated filer"],
                        ["SRC", seg.find("sml"), "sml", "smaller reporting company"]]
        sortedlist = sorted(sorterlister, key=lambda position: position[1])

    ##        print(seg)
    ##        print(sortedlist)
    if sortedlist == [] or len(sortedlist) == 1:
        return "no filer category information"
    while sortedlist[0][1] == -1 and len(sortedlist) != 1:
        del sortedlist[0]
    if sortedlist == [] or len(sortedlist) == 1:
        return "no filer category information"

    if sortedlist[0][1] == 0:
        starts = True
    else:
        starts = False
    point = 0
    for elem in range(len(sortedlist)):
        if starts:
            if elem != len(sortedlist) - 1:
                filertyper.append([sortedlist[elem][0],
                                   seg[sortedlist[elem][1] + len(sortedlist[elem][2]):sortedlist[elem + 1][1]].strip(),
                                   sortedlist[elem][3]])
            else:
                filertyper.append([sortedlist[elem][0], seg[sortedlist[elem][1] + len(sortedlist[elem][2]):].strip(),
                                   sortedlist[elem][3]])
        else:
            if elem == 0:
                filertyper.append([sortedlist[elem][0], seg[:sortedlist[elem][1]].strip(), sortedlist[elem][3]])
            else:
                filertyper.append([sortedlist[elem][0], seg[sortedlist[elem - 1][1] + len(sortedlist[elem - 1][2]):
                                                            sortedlist[elem][1]].strip(), sortedlist[elem][3]])
    ##    print(filertyper)
    filertyper.sort()
    for row in filertyper:
        for fsm in filestatusmarks:
            if fsm in row[1]:
                ##                print("next observation")
                ##                print(filertyper)
                ##                print(fsm)
                ##                print(row[2])
                return row[2]
    if mode == 1:
        ##        print(filertyper)
        if "x" in filertyper[1][1] or "Ã" in filertyper[1][1] or "þ" in filertyper[1][1] or "ý" in filertyper[1][
            1] or "ü" in filertyper[1][1]:
            file = "accelerated filer"
            return file
        if "x" in filertyper[0][1] or "Ã" in filertyper[0][1] or "þ" in filertyper[0][1] or "ý" in filertyper[0][
            1] or "ü" in filertyper[0][1]:
            file = "not an accelerated filer"
            return file
    ##        if file =="":
    ##            print(seg, filertyper)
    else:
        ##        print("filertyper", filertyper)
        comparer = []
        for item in filertyper:
            comparer.append(item[1].strip())
        for element in range(len(comparer)):
            comparer2 = []
            if element != 0:
                comparer2 = comparer[:element]
            if element != len(comparer) - 1:
                comparer2.extend(comparer[element + 1:])
            ##            print("comparer", comparer)
            ##            print("comparer 2", comparer2)

            if comparer2.count(comparer2[0]) == len(comparer2) and comparer[element] != comparer2[0]:
                ##                print(filertyper[element][2])
                return filertyper[element][2]
    ##        print(comparer)
    ##    for word in breaks:
    ##        if seg[0] == word[0]:
    ##            starts = True
    ##            break
    ##    indx = 0
    ##    categ = "none"
    ##    while categ=="none":
    ##        categ = whichword(breaks, seg[indx:])
    ##        if categ=="none":
    ##            indx+=1
    ##    if starts != 0:
    ##        filertyper.append([categ, seg[:indx]])
    ##    else:
    ##        seg2 = seg[indx+1:]
    ##        indx2 = 0
    ##        categ2 = "none"
    ##        while categ2=="none":
    ##            categ2 = whichword(breaks, seg2[indx2:])
    ##            if categ2=="none":
    ##                indx2+=1
    ##        filertyper.append([categ, seg2[:indx2]])
    ##

    return file


def whichword(listed, segment):
    for word in listed:
        if segment[0] == word[0]:
            return word
    return "none"


def main():
    ##    global mode
    ##    mode = input("Enter 1 to attempt alternate downloading.  Enter anything else not to:")
    ##
    ##    print(type(mode))
    ##    print(mode)

    ##    for year in range(1994,2016):
    for year in range(2014, 2016):
        for quarter in range(1, 5):
            ##            year = 2003
            ##            quarter = 1
            ##            if year ==2007 and quarter==1:
            ##                continue
            ##            global alternate_exists
            ##            alternate_exists= 0
            if not os.path.exists("%s_%s.csv" % (year, quarter)):
                readindex(year, quarter)
            print(year, quarter)
            ##            readindex(year, quarter)
            readforms(year, quarter)
    print(datetime.datetime.now())


def removeNonAscii(s):
    return "".join(i for i in s if ord(i) < 128)


if __name__ == '__main__':
    main()
